"""
Módulo para gerenciar usuários no Firebase Firestore.
Responsável por criar, buscar, atualizar e verificar usuários.
"""

import logging
import datetime
from firebase_admin import firestore
import bcrypt
from django.conf import settings

# Configurar logger
logger = logging.getLogger(__name__)

# Nome da coleção de usuários
USERS_COLLECTION = 'users'

class UserManager:
    """
    Classe para gerenciar usuários no Firebase Firestore
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de usuários e conecta ao Firestore
        """
        try:
            from core.firebase_config import initialize_firebase
            self.db = initialize_firebase()
            self.collection = self.db.collection(USERS_COLLECTION)
            logger.info("UserManager inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar UserManager: {str(e)}")
            raise
    
    def create_user(self, cpf, senha, id_contato_bling, nome=None, email=None, telefone=None, perfil='cliente'):
        """
        Cria um novo usuário na coleção users
        
        Args:
            cpf: CPF do usuário (sem formatação)
            senha: Senha em texto puro (será armazenada com hash)
            id_contato_bling: ID do contato no sistema Bling
            nome: Nome do usuário (opcional)
            email: Email do usuário (opcional)
            telefone: Telefone do usuário (opcional)
            perfil: Tipo de perfil (default: cliente)
            
        Returns:
            str: ID do documento criado ou None em caso de erro
        """
        try:
            # Verifica se o CPF já existe
            if self.get_user_by_cpf(cpf):
                logger.warning(f"Tentativa de criar usuário com CPF já existente: {cpf}")
                return None
            
            # Gera o hash da senha
            senha_hash = self._hash_password(senha)
            
            # Prepara o documento de usuário
            user_doc = {
                "cpf": cpf,
                "senha_hash": senha_hash,
                "id_contato_bling": id_contato_bling,
                "data_cadastro": firestore.SERVER_TIMESTAMP,
                "status": "ativo",
                "perfil": perfil
            }
            
            # Adiciona campos opcionais se fornecidos
            if nome:
                user_doc["nome"] = nome
            if email:
                user_doc["email"] = email
            if telefone:
                user_doc["telefone"] = telefone
                
            # Adiciona metadados
            user_doc["metadata"] = {
                "versao_app": settings.APP_VERSION if hasattr(settings, 'APP_VERSION') else "1.0.0",
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            }
            
            # Adiciona o documento ao Firestore
            doc_ref = self.collection.document(cpf)
            doc_ref.set(user_doc)
            
            logger.info(f"Usuário criado com sucesso. CPF: {cpf}")
            return cpf
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            return None
    
    def get_user_by_cpf(self, cpf):
        """
        Busca um usuário pelo CPF
        
        Args:
            cpf: CPF do usuário (sem formatação)
            
        Returns:
            dict: Dados do usuário ou None se não encontrado
        """
        try:
            doc_ref = self.collection.document(cpf)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                logger.info(f"Usuário não encontrado. CPF: {cpf}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por CPF: {str(e)}")
            return None
    
    def update_user(self, cpf, data):
        """
        Atualiza dados de um usuário existente
        
        Args:
            cpf: CPF do usuário (sem formatação)
            data: Dicionário com os campos a serem atualizados
            
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        try:
            # Verifica se o usuário existe
            if not self.get_user_by_cpf(cpf):
                logger.warning(f"Tentativa de atualizar usuário inexistente. CPF: {cpf}")
                return False
            
            # Campos que não podem ser atualizados
            protected_fields = ['cpf', 'data_cadastro']
            
            # Remove campos protegidos
            update_data = {k: v for k, v in data.items() if k not in protected_fields}
            
            # Se estiver tentando atualizar a senha, gera o hash
            if 'senha' in update_data:
                update_data['senha_hash'] = self._hash_password(update_data.pop('senha'))
            
            # Atualiza o documento
            doc_ref = self.collection.document(cpf)
            doc_ref.update(update_data)
            
            logger.info(f"Usuário atualizado com sucesso. CPF: {cpf}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário: {str(e)}")
            return False
    
    def verify_password(self, cpf, senha):
        """
        Verifica se a senha fornecida corresponde à senha armazenada
        
        Args:
            cpf: CPF do usuário (sem formatação)
            senha: Senha em texto puro para verificar
            
        Returns:
            bool: True se a senha estiver correta, False caso contrário
        """
        try:
            # Busca o usuário
            user = self.get_user_by_cpf(cpf)
            if not user:
                logger.warning(f"Tentativa de verificar senha para usuário inexistente. CPF: {cpf}")
                return False
            
            # Verifica o status do usuário
            if user.get('status') != 'ativo':
                logger.warning(f"Tentativa de login em usuário inativo. CPF: {cpf}")
                return False
            
            # Obtém o hash armazenado
            stored_hash = user.get('senha_hash')
            if not stored_hash:
                logger.error(f"Usuário sem senha definida. CPF: {cpf}")
                return False
            
            # Verifica a senha
            senha_bytes = senha.encode('utf-8')
            stored_hash_bytes = stored_hash.encode('utf-8')
            
            # Verifica se a senha corresponde ao hash
            result = bcrypt.checkpw(senha_bytes, stored_hash_bytes)
            
            # Atualiza a data do último acesso em caso de sucesso
            if result:
                self.collection.document(cpf).update({
                    'ultimo_acesso': firestore.SERVER_TIMESTAMP
                })
                logger.info(f"Login bem-sucedido. CPF: {cpf}")
            else:
                logger.warning(f"Tentativa de login com senha incorreta. CPF: {cpf}")
                
            return result
            
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {str(e)}")
            return False
    
    def deactivate_user(self, cpf):
        """
        Desativa um usuário (sem excluí-lo)
        
        Args:
            cpf: CPF do usuário (sem formatação)
            
        Returns:
            bool: True se desativado com sucesso, False caso contrário
        """
        try:
            # Verifica se o usuário existe
            if not self.get_user_by_cpf(cpf):
                logger.warning(f"Tentativa de desativar usuário inexistente. CPF: {cpf}")
                return False
            
            # Atualiza o status para inativo
            doc_ref = self.collection.document(cpf)
            doc_ref.update({
                'status': 'inativo',
                'data_desativacao': firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Usuário desativado com sucesso. CPF: {cpf}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desativar usuário: {str(e)}")
            return False
    
    def _hash_password(self, password):
        """
        Gera um hash seguro para a senha
        
        Args:
            password: Senha em texto puro
            
        Returns:
            str: Hash da senha
        """
        try:
            # Converte a senha para bytes
            password_bytes = password.encode('utf-8')
            
            # Gera o salt e o hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Retorna como string
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erro ao gerar hash de senha: {str(e)}")
            raise
    
    def create_collection(self):
        """
        Cria a coleção de usuários se não existir
        
        Returns:
            bool: True se a coleção foi criada/já existe, False em caso de erro
        """
        try:
            # Verifica se a coleção existe criando um documento temporário
            temp_doc = self.collection.document('_temp')
            temp_doc.set({'init': True})
            temp_doc.delete()
            
            logger.info("Coleção 'users' inicializada com sucesso.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar coleção 'users': {str(e)}")
            return False