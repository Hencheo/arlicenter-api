"""
Módulo de configuração para o Firebase Admin SDK.
Responsável por inicializar e configurar a conexão com o Firebase.
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Caminho para o diretório do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Variável para armazenar a instância do Firestore
db = None

# Nome da coleção para armazenar tokens do Bling
BLING_TOKENS_COLLECTION = 'bling_tokens'

def get_firebase_credentials_path():
    """
    Retorna o caminho para o arquivo de credenciais do Firebase.
    Tenta obter das configurações do Django ou cria um arquivo a partir de variáveis de ambiente.
    
    Returns:
        str: Caminho absoluto para o arquivo de credenciais
    """
    # Se o caminho estiver definido nas configurações
    if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and settings.FIREBASE_CREDENTIALS_PATH:
        return settings.FIREBASE_CREDENTIALS_PATH
    
    # Se temos as credenciais como string JSON em uma variável de ambiente
    firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
    if firebase_credentials_json:
        try:
            # Diretório para armazenar as credenciais
            credentials_dir = Path(settings.BASE_DIR) / 'credentials'
            credentials_dir.mkdir(exist_ok=True)
            
            # Caminho do arquivo
            credentials_path = credentials_dir / 'firebase-credentials.json'
            
            # Converter a string JSON em um objeto Python
            credentials_data = json.loads(firebase_credentials_json)
            
            # Salvar no arquivo
            with open(credentials_path, 'w') as f:
                json.dump(credentials_data, f)
            
            logger.info(f"Credenciais do Firebase salvas em {credentials_path}")
            return str(credentials_path)
            
        except Exception as e:
            logger.error(f"Erro ao processar credenciais do Firebase: {str(e)}")
    
    # Local padrão se nada funcionar
    default_path = os.path.join(settings.BASE_DIR, 'credentials', 'firebase-credentials.json')
    logger.warning(f"Usando caminho padrão para credenciais do Firebase: {default_path}")
    return default_path

def initialize_firebase():
    """
    Inicializa o Firebase Admin SDK e retorna um cliente Firestore.
    
    Returns:
        firestore.Client: Cliente do Firestore para interagir com o banco de dados
    """
    global db
    
    # Se já temos uma instância do Firestore, retorne-a
    if db is not None:
        return db
    
    try:
        # Verifica se já foi inicializado
        if not firebase_admin._apps:
            try:
                # Obtém o caminho para as credenciais
                cred_path = get_firebase_credentials_path()
                
                # Verifica se o arquivo existe
                if not os.path.exists(cred_path):
                    logger.error(f"Arquivo de credenciais do Firebase não encontrado: {cred_path}")
                    raise FileNotFoundError(f"Arquivo de credenciais do Firebase não encontrado: {cred_path}")
                
                # Inicializa o SDK do Firebase com as credenciais
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK inicializado com sucesso")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao ler o arquivo de credenciais JSON: {e}")
                raise
            except Exception as e:
                logger.error(f"Erro na inicialização do Firebase Admin SDK: {e}")
                raise
        
        # Obtém e armazena o cliente Firestore
        db = firestore.client()
        return db
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Firebase: {str(e)}")
        # Tentativa de criar um objeto mock para evitar falhas críticas
        try:
            from unittest.mock import MagicMock
            mock_db = MagicMock()
            logger.warning("Usando cliente Firestore mockado devido a falha na inicialização")
            return mock_db
        except ImportError:
            # Se não conseguir importar mock, repassamos a exceção
            raise 