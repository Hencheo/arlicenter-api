import os
import django

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arlicenter.settings')
django.setup()

# Importar o TokenManager após configurar o Django
from core.token_manager import TokenManager

# Criar uma instância do TokenManager
token_manager = TokenManager()

# Chamar o método delete_all_tokens
num_deleted = token_manager.delete_all_tokens()

print(f"Foram excluídos {num_deleted} tokens.") 