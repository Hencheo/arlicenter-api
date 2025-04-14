#!/usr/bin/env python
"""
Script para validar a conexão com o Firebase.
Este script pode ser executado independentemente para verificar se as credenciais do Firebase estão corretas 
e se a conexão com o Firestore pode ser estabelecida.
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
from core.firebase_config import initialize_firebase

def validate_firebase_connection():
    """
    Testa a conexão com o Firebase/Firestore.
    """
    try:
        # Inicializa o Firebase
        db = initialize_firebase()
        
        # Tenta criar uma coleção de teste
        test_ref = db.collection('test_connection').document('test_doc')
        test_ref.set({
            'timestamp': django.utils.timezone.now().isoformat(),
            'message': 'Conexão de teste bem-sucedida'
        })
        
        # Lê o documento para confirmar a escrita
        test_doc = test_ref.get()
        if test_doc.exists:
            print("✅ Conexão com o Firebase estabelecida com sucesso!")
            print(f"Dados do documento: {test_doc.to_dict()}")
            
            # Limpa o documento de teste
            test_ref.delete()
            return True
        else:
            print("❌ Falha ao ler o documento de teste após a escrita.")
            return False
    
    except Exception as e:
        print(f"❌ Erro ao validar conexão com o Firebase: {e}")
        return False

if __name__ == "__main__":
    print("Validando conexão com o Firebase...")
    if validate_firebase_connection():
        print("Validação concluída com sucesso.")
        sys.exit(0)
    else:
        print("Falha na validação da conexão. Verifique as credenciais e a configuração.")
        sys.exit(1) 