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
                return self.refresh_token(token_data)
            
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
    
    def refresh_token(self, token_data):
        """
        Atualiza o token usando o refresh_token
        
        Args:
            token_data (dict): Dados do token antigo
            
        Returns:
            dict: Dados do novo token ou None se falhar
        """
        try:
            # Implementar lógica de refresh do token
            # Esta é uma função placeholder - você precisará implementar a chamada 
            # à API do Bling para atualizar o token usando o refresh_token
            
            # TODO: Implementar chamada de refresh do token
            
            logger.error("Função de refresh do token não implementada")
            return token_data  # Por enquanto, retorna o token original
            
        except Exception as e:
            logger.error(f"Erro ao atualizar token: {str(e)}")
            return token_data  # Retorna o token original em caso de erro
    
    def _save_token_locally(self, token_data):
        """
        Salva o token localmente como fallback
        
        Args:
            token_data (dict): Dados do token
        """
        try:
            # Cria o diretório se não existir
            tokens_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens'))
            tokens_dir.mkdir(exist_ok=True)
            
            # Cria um nome de arquivo com timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"token_{timestamp}.json"
            filepath = tokens_dir / filename
            
            # Salva o token como JSON
            with open(filepath, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            logger.info(f"Token salvo localmente como fallback: {filepath}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar token localmente: {str(e)}")
            # Tenta salvar em /tmp como último recurso
            try:
                tmp_dir = Path('/tmp/bling_tokens')
                tmp_dir.mkdir(exist_ok=True, parents=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"token_{timestamp}.json"
                filepath = tmp_dir / filename
                
                with open(filepath, 'w') as f:
                    json.dump(token_data, f, indent=2)
                    
                logger.info(f"Token salvo em diretório temporário: {filepath}")
            except Exception as inner_e:
                logger.critical(f"Falha em todas as tentativas de salvar o token: {str(inner_e)}")
    
    def _get_local_token(self):
        """
        Obtém o token mais recente salvo localmente
        
        Returns:
            dict: Dados do token ou None se não encontrado
        """
        try:
            # Diretórios para procurar tokens
            tokens_dirs = [
                Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens')),
                Path('/tmp/bling_tokens')
            ]
            
            latest_file = None
            latest_time = datetime.datetime.min
            
            # Procura em ambos os diretórios
            for tokens_dir in tokens_dirs:
                if not tokens_dir.exists():
                    continue
                    
                # Lista todos os arquivos JSON no diretório
                for file in tokens_dir.glob('token_*.json'):
                    file_time = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = file
            
            # Se encontrou um arquivo, lê o conteúdo
            if latest_file:
                with open(latest_file, 'r') as f:
                    token_data = json.load(f)
                    logger.info(f"Token obtido localmente: {latest_file}")
                    return token_data
            
            logger.warning("Nenhum token local encontrado")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter token local: {str(e)}")
            return None

    def create_token_collection(self):
        """
        Cria a coleção de tokens no Firestore se ela não existir.
        No Firestore, as coleções são criadas implicitamente quando documentos são adicionados,
        então esta função serve principalmente para verificar a conexão e registrar a operação.
        """
        try:
            # Criamos um documento temporário para verificar se a coleção pode ser acessada
            temp_doc = self.collection.document('_temp_initialization')
            temp_doc.set({
                'created_at': firestore.SERVER_TIMESTAMP,
                'description': 'Documento temporário para inicialização da coleção'
            })
            
            # Deletamos o documento temporário
            temp_doc.delete()
            
            logger.info(f"Coleção '{BLING_TOKENS_COLLECTION}' inicializada com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar coleção '{BLING_TOKENS_COLLECTION}': {str(e)}")
            return False
            
    def define_token_structure(self):
        """
        Define a estrutura do documento para armazenar tokens.
        Esta função é informativa e retorna a estrutura de dados esperada.
        """
        # No Firestore, não precisamos definir um esquema antecipadamente,
        # mas é útil documentar a estrutura esperada
        token_structure = {
            'access_token': 'string - Token de acesso',
            'refresh_token': 'string - Token de atualização',
            'expires_in': 'number - Tempo de expiração em segundos',
            'expires_at': 'timestamp - Data/hora de expiração (calculada)',
            'created_at': 'timestamp - Data/hora de criação',
            'updated_at': 'timestamp - Data/hora da última atualização',
            'is_active': 'boolean - Indica se é o token ativo atual',
            'token_type': 'string - Tipo de token (ex: "bearer")',
            'scope': 'string - Escopo do token'
        }
        
        logger.info(f"Estrutura de documento definida para '{BLING_TOKENS_COLLECTION}'")
        return token_structure
        
    def update_token(self, token_data, refresh_token=None):
        """
        Atualiza o token usando o refresh_token.
        
        Args:
            token_data (dict): Novos dados do token.
            refresh_token (str, optional): Token de atualização. Se não fornecido, usa o do token ativo.
            
        Returns:
            bool: True se o token foi atualizado com sucesso, False caso contrário.
        """
        try:
            # Desativa tokens ativos anteriores
            self._deactivate_active_tokens()
            
            # Adiciona metadados ao token
            token_with_metadata = token_data.copy()
            token_with_metadata.update({
                'created_at': firestore.SERVER_TIMESTAMP,
                'is_active': True,
                'last_used': firestore.SERVER_TIMESTAMP,
                'refreshed_from': refresh_token
            })
            
            # Adiciona o novo token ao Firestore
            doc_ref = self.collection.add(token_with_metadata)
            
            logger.info(f"Token atualizado com sucesso. Novo ID: {doc_ref[1].id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar token: {str(e)}")
            return False

    def create_firestore_indexes(self):
        """
        Cria índices necessários para consultas eficientes.
        No Firestore, os índices compostos precisam ser criados manualmente
        no console do Firebase, mas esta função documenta quais índices são necessários.
        
        Returns:
            dict: Descrição dos índices recomendados
        """
        # No Firestore, os índices simples são criados automaticamente
        # e os compostos precisam ser criados no console do Firebase
        recommended_indexes = {
            "single_field": [
                {"field": "is_active", "order": "ASCENDING"},
                {"field": "created_at", "order": "DESCENDING"},
                {"field": "expires_at", "order": "ASCENDING"}
            ],
            "composite": [
                {
                    "name": "active_tokens_by_expiration",
                    "fields": [
                        {"field": "is_active", "order": "ASCENDING"},
                        {"field": "expires_at", "order": "ASCENDING"}
                    ]
                },
                {
                    "name": "tokens_by_creation_date",
                    "fields": [
                        {"field": "is_active", "order": "ASCENDING"},
                        {"field": "created_at", "order": "DESCENDING"}
                    ]
                }
            ]
        }
        
        logger.info("Índices recomendados para a coleção de tokens documentados")
        return recommended_indexes 