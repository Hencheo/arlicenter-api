"""
Módulo para gerenciar tokens do Bling no Firestore.
Responsável por salvar, atualizar, consultar e gerenciar os tokens de acesso.
"""

import logging
import datetime
from django.utils import timezone
from firebase_admin import firestore
try:
    from core.firebase_config import initialize_firebase, BLING_TOKENS_COLLECTION
except ImportError:
    # Fallback para importação relativa
    try:
        from .firebase_config import initialize_firebase, BLING_TOKENS_COLLECTION
    except ImportError as e:
        logging.error(f"Não foi possível importar firebase_config: {e}")
        # Valores padrão para caso a importação falhe
        BLING_TOKENS_COLLECTION = 'bling_tokens'
        def initialize_firebase():
            logging.error("Firebase não inicializado corretamente.")
            return None
import firebase_admin
from firebase_admin import credentials
import os
from django.conf import settings
import json
from pathlib import Path
import requests
import base64

# Configurar logger
logger = logging.getLogger(__name__)

class TokenManager:
    """
    Classe para gerenciar tokens do Bling no Firebase Firestore
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de tokens e conecta ao Firestore
        """
        try:
            self.db = initialize_firebase()
            self.collection = self.db.collection(BLING_TOKENS_COLLECTION)
            logger.info("TokenManager inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar TokenManager: {str(e)}")
            raise
    
    def create_token_document(self, token_data):
        """
        Cria um novo documento de token no Firestore e desativa tokens anteriores
        
        Args:
            token_data (dict): Dados do token recebidos da API Bling
            
        Returns:
            str: ID do documento criado
        """
        try:
            # Adiciona metadados ao token
            token_doc = {
                **token_data,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_used': firestore.SERVER_TIMESTAMP,
                'active': True
            }
            
            # Desativa tokens ativos anteriores
            self._deactivate_active_tokens()
            
            # Adiciona o novo token
            doc_ref = self.collection.add(token_doc)
            token_id = doc_ref[1].id
            
            logger.info(f"Token criado com sucesso. ID: {token_id}")
            return token_id
            
        except Exception as e:
            logger.error(f"Erro ao criar token no Firestore: {str(e)}")
            # Salvar localmente como fallback
            self._save_token_locally(token_data)
            raise
    
    def _deactivate_active_tokens(self):
        """
        Desativa todos os tokens ativos no Firestore
        """
        try:
            # Busca todos os tokens ativos
            active_tokens = self.collection.where('active', '==', True).stream()
            
            # Para cada token ativo, marca como inativo
            batch = self.db.batch()
            for token in active_tokens:
                token_ref = self.collection.document(token.id)
                batch.update(token_ref, {'active': False})
            
            # Executa o batch
            batch.commit()
            logger.info("Tokens anteriores desativados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao desativar tokens ativos: {str(e)}")
    
    def get_active_token(self):
        """
        Obtém o token ativo mais recente
        
        Returns:
            dict: Dados do token ou None se não encontrado
        """
        try:
            # Busca o token ativo mais recente ordenado por data de criação
            query = self.collection.where('active', '==', True).order_by('created_at', direction=firestore.Query.DESCENDING).limit(1)
            tokens = list(query.stream())
            
            if not tokens:
                logger.warning("Nenhum token ativo encontrado")
                return None
            
            # Obtém o primeiro token da lista
            token_doc = tokens[0]
            token_id = token_doc.id
            token_data = token_doc.to_dict()
            
            # Atualiza a data de último uso
            self.collection.document(token_id).update({
                'last_used': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Token ativo recuperado com sucesso. ID: {token_id}")
            
            # Verifica se o token precisa ser atualizado
            if self.should_refresh_token(token_data):
                logger.info("Token precisa ser atualizado. Iniciando refresh...")
                refresh_result = self.refresh_token(token_data.get('refresh_token'))
                if refresh_result:
                    # Retorna o token atualizado
                    return self.get_active_token()
            
            return token_data
            
        except Exception as e:
            logger.error(f"Erro ao obter token ativo: {str(e)}")
            # Tenta obter token localmente como fallback
            return self._get_local_token()
    
    def should_refresh_token(self, token_data):
        """
        Verifica se um token deve ser atualizado baseado na data de criação e tempo de expiração
        
        Args:
            token_data (dict): Dados do token
            
        Returns:
            bool: True se o token deve ser atualizado, False caso contrário
        """
        try:
            # Obtém a data de criação do token
            created_at = token_data.get('created_at')
            if not created_at:
                return True
                
            # Converte para datetime se for um timestamp do Firestore
            if isinstance(created_at, firestore.SERVER_TIMESTAMP):
                created_at = datetime.datetime.now()
            
            # Tempo de expiração em segundos
            expires_in = token_data.get('expires_in', 3600)
            
            # Calcula tempo restante (margem de segurança de 10 minutos)
            expiry_time = created_at + datetime.timedelta(seconds=expires_in)
            refresh_time = expiry_time - datetime.timedelta(minutes=10)
            
            # Verifica se está na hora de atualizar
            current_time = datetime.datetime.now()
            return current_time >= refresh_time
            
        except Exception as e:
            logger.error(f"Erro ao verificar necessidade de atualização do token: {str(e)}")
            # Em caso de erro, é mais seguro dizer que sim
            return True
    
    def refresh_token(self, refresh_token):
        """
        Atualiza o token usando o refresh_token
        
        Args:
            refresh_token (str): Token de atualização
            
        Returns:
            bool: True se o token foi atualizado com sucesso, False caso contrário
        """
        try:
            # Verifica se temos um refresh_token
            if not refresh_token:
                logger.error("Impossível renovar token: refresh_token não fornecido")
                return False
            
            # Obtém as credenciais do cliente
            client_id = settings.BLING_CLIENT_ID
            client_secret = settings.BLING_CLIENT_SECRET
            
            if not client_id or not client_secret:
                logger.error("Credenciais do Bling não configuradas")
                return False
            
            # Configura a requisição
            url = "https://api.bling.com.br/Api/v3/oauth/token"
            
            # Cria o cabeçalho de autenticação
            auth_str = f"{client_id}:{client_secret}"
            auth_bytes = auth_str.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            # Dados do corpo da requisição
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            # Realiza a requisição
            logger.info(f"Realizando requisição de renovação de token")
            response = requests.post(url, data=data, headers=headers)
            
            # Verifica se a requisição foi bem-sucedida
            if response.status_code != 200:
                logger.error(f"Erro ao renovar token: {response.status_code} - {response.text}")
                return False
            
            # Obtém os dados do novo token
            token_data = response.json()
            
            # Salva o novo token
            self.create_token_document(token_data)
            
            logger.info("Token renovado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao renovar token: {str(e)}")
            return False
    
    def _save_token_locally(self, token_data):
        """
        Salva o token em um arquivo local como fallback
        
        Args:
            token_data (dict): Dados do token
        """
        try:
            # Define o diretório para salvar os tokens
            try:
                tokens_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens'))
                tokens_dir.mkdir(exist_ok=True)
            except Exception as dir_error:
                logger.warning(f"Não foi possível criar o diretório bling_tokens: {str(dir_error)}")
                tokens_dir = Path(os.path.join('/tmp', 'bling_tokens'))
                tokens_dir.mkdir(exist_ok=True)
            
            # Define o nome do arquivo baseado na data/hora atual
            filename = tokens_dir / f"token_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Adiciona metadados ao token
            token_data_with_metadata = {
                **token_data,
                'created_at': datetime.datetime.now().isoformat(),
                'last_used': datetime.datetime.now().isoformat(),
                'active': True
            }
            
            # Salva o token no arquivo
            with open(filename, 'w') as f:
                json.dump(token_data_with_metadata, f, indent=4)
            
            # Salva também um arquivo com nome fixo para facilitar recuperação
            active_filename = tokens_dir / "token_active.json"
            with open(active_filename, 'w') as f:
                json.dump(token_data_with_metadata, f, indent=4)
            
            logger.info(f"Token salvo localmente em {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar token localmente: {str(e)}")
    
    def _get_local_token(self):
        """
        Obtém o token salvo localmente como fallback
        
        Returns:
            dict: Dados do token ou None se não encontrado
        """
        try:
            # Define o diretório dos tokens
            tokens_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens'))
            if not tokens_dir.exists():
                tokens_dir = Path(os.path.join('/tmp', 'bling_tokens'))
                if not tokens_dir.exists():
                    logger.warning("Diretório de tokens não encontrado")
                    return None
            
            # Tenta ler o arquivo fixo primeiro
            active_filename = tokens_dir / "token_active.json"
            if active_filename.exists():
                with open(active_filename, 'r') as f:
                    token_data = json.load(f)
                logger.info("Token recuperado do arquivo local fixo")
                return token_data
            
            # Se não encontrar, busca o arquivo mais recente
            token_files = list(tokens_dir.glob("token_*.json"))
            if not token_files:
                logger.warning("Nenhum arquivo de token encontrado")
                return None
            
            # Ordena por data de modificação (mais recente primeiro)
            token_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Lê o arquivo mais recente
            with open(token_files[0], 'r') as f:
                token_data = json.load(f)
            
            logger.info(f"Token recuperado do arquivo local: {token_files[0]}")
            return token_data
            
        except Exception as e:
            logger.error(f"Erro ao obter token local: {str(e)}")
            return None
    
    def create_token_collection(self):
        """
        Cria a coleção de tokens no Firestore
        
        Returns:
            bool: True se a coleção foi criada com sucesso, False caso contrário
        """
        try:
            # Verifica se a coleção existe criando um documento temporário
            temp_doc = self.collection.document('_temp')
            temp_doc.set({'init': True})
            temp_doc.delete()
            
            # Define a estrutura padrão da coleção
            self.define_token_structure()
            
            # Cria índices
            self.create_firestore_indexes()
            
            logger.info(f"Coleção '{BLING_TOKENS_COLLECTION}' inicializada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar coleção '{BLING_TOKENS_COLLECTION}': {str(e)}")
            return False
    
    def define_token_structure(self):
        """
        Define a estrutura padrão de um documento de token
        """
        try:
            # Cria um documento de exemplo com a estrutura esperada
            token_structure = {
                'access_token': '',
                'token_type': 'bearer',
                'expires_in': 3600,
                'refresh_token': '',
                'scope': '',
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_used': firestore.SERVER_TIMESTAMP,
                'active': False
            }
            
            # Adiciona o documento de estrutura
            structure_doc = self.collection.document('_structure')
            structure_doc.set(token_structure)
            
            logger.info(f"Estrutura da coleção '{BLING_TOKENS_COLLECTION}' definida com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao definir estrutura da coleção: {str(e)}")
    
    def update_token(self, token_data, refresh_token=None):
        """
        Atualiza um token existente
        
        Args:
            token_data (dict): Dados do token
            refresh_token (str): Token de atualização (opcional)
            
        Returns:
            bool: True se o token foi atualizado com sucesso, False caso contrário
        """
        try:
            # Busca os tokens ativos
            query = self.collection.where('active', '==', True).limit(1)
            tokens = list(query.stream())
            
            if not tokens:
                logger.warning("Nenhum token ativo encontrado para atualização")
                # Se não encontrar tokens ativos, cria um novo
                if refresh_token:
                    return self.refresh_token(refresh_token)
                else:
                    return self.create_token_document(token_data)
            
            # Obtém o token ativo
            token_doc = tokens[0]
            token_id = token_doc.id
            
            # Atualiza o token
            token_data['last_used'] = firestore.SERVER_TIMESTAMP
            self.collection.document(token_id).update(token_data)
            
            logger.info(f"Token atualizado com sucesso. ID: {token_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar token: {str(e)}")
            return False
    
    def create_firestore_indexes(self):
        """
        Cria índices no Firestore para otimizar consultas frequentes
        
        Returns:
            bool: True se os índices foram criados com sucesso, False caso contrário
        """
        # Este método é apenas para documentação, pois a criação de índices
        # é geralmente feita através do console do Firebase ou de regras específicas
        # No ambiente real, os índices necessários são:
        # - active (ascendente) + created_at (descendente)
        logger.info("Índices para o Firestore devem ser criados manualmente no console do Firebase")
        logger.info("- Índice em 'active' (ascendente) + 'created_at' (descendente)")
        
        return True