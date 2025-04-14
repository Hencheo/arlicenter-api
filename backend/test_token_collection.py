#!/usr/bin/env python
"""
Script para testar a criação e manipulação da coleção de tokens no Firestore.
"""

import os
import sys
import django
from pathlib import Path

# Adiciona o diretório pai ao path para poder importar o projeto Django
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arlicenter.settings")
django.setup()

# Agora podemos importar do projeto Django
from core.token_manager import TokenManager

def test_token_collection():
    """
    Testa a criação e manipulação da coleção de tokens no Firestore.
    """
    print("\n=== Testando Coleção de Tokens no Firestore ===")
    
    # Inicializa o gerenciador de tokens
    token_manager = TokenManager()
    
    # Testa a criação da coleção
    print("\n1. Testando criação da coleção...")
    if token_manager.create_token_collection():
        print("✅ Coleção de tokens criada/acessada com sucesso!")
    else:
        print("❌ Falha ao criar/acessar coleção de tokens")
        return False
    
    # Exibe a estrutura do documento
    print("\n2. Estrutura do documento de token:")
    structure = token_manager.define_token_structure()
    for field, description in structure.items():
        print(f"   - {field}: {description}")
    
    # Testa a criação de um documento de token
    print("\n3. Testando criação de um documento de token...")
    test_token_data = {
        'access_token': 'test_access_token_123',
        'refresh_token': 'test_refresh_token_456',
        'expires_in': 3600,
        'token_type': 'bearer',
        'scope': 'all'
    }
    
    doc_id = token_manager.create_token_document(test_token_data)
    if doc_id:
        print(f"✅ Documento de token criado com sucesso! ID: {doc_id}")
    else:
        print("❌ Falha ao criar documento de token")
        return False
    
    # Testa a desativação de tokens anteriores
    print("\n4. Testando desativação de tokens anteriores...")
    # Criamos um segundo token para testar a desativação
    second_token_data = {
        'access_token': 'test_access_token_789',
        'refresh_token': 'test_refresh_token_012',
        'expires_in': 3600,
        'token_type': 'bearer',
        'scope': 'all'
    }
    
    # Este deve desativar o token anterior
    second_doc_id = token_manager.create_token_document(second_token_data)
    if second_doc_id:
        print(f"✅ Segundo documento de token criado com sucesso! ID: {second_doc_id}")
        print("✅ O primeiro token deve ter sido desativado automaticamente")
    else:
        print("❌ Falha ao criar segundo documento de token")
        return False
    
    # Exibe os índices recomendados
    print("\n5. Índices recomendados:")
    indexes = token_manager.create_firestore_indexes()
    
    print("   Índices de campo único:")
    for idx in indexes["single_field"]:
        print(f"   - Campo: {idx['field']}, Ordem: {idx['order']}")
    
    print("\n   Índices compostos:")
    for idx in indexes["composite"]:
        print(f"   - Nome: {idx['name']}")
        print(f"     Campos: {', '.join([f'{f['field']} ({f['order']})' for f in idx['fields']])}")
    
    print("\n=== Testes concluídos com sucesso! ===")
    return True

if __name__ == "__main__":
    if test_token_collection():
        sys.exit(0)
    else:
        print("\n❌ Teste da coleção de tokens falhou")
        sys.exit(1) 