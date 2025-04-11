#!/usr/bin/env python
"""
Script para testar as funcionalidades do UserManager
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Tenta configurar o Django (pode falhar se não estiver em um ambiente Django)
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arlicenter.settings')
    import django
    django.setup()
    print("Django configurado com sucesso.")
except Exception as e:
    print(f"Aviso: Não foi possível configurar o Django: {str(e)}")
    print("O script continuará, mas algumas funcionalidades podem não estar disponíveis.")

# Agora importa o UserManager
try:
    from core.user_manager import UserManager
    from core.firebase_config import initialize_firebase
    print("UserManager importado com sucesso.")
except Exception as e:
    print(f"Erro ao importar UserManager: {str(e)}")
    sys.exit(1)

def testar_criar_colecao():
    """
    Testa a criação da coleção de usuários
    """
    print("\n=== Testando criação da coleção de usuários ===")
    user_manager = UserManager()
    resultado = user_manager.create_collection()
    print(f"Resultado: {'Sucesso' if resultado else 'Falha'}")
    return resultado

def testar_criar_usuario(cpf, senha, id_contato_bling, nome=None, email=None, telefone=None):
    """
    Testa a criação de um novo usuário
    """
    print(f"\n=== Testando criação de usuário com CPF {cpf} ===")
    user_manager = UserManager()
    
    resultado = user_manager.create_user(
        cpf=cpf,
        senha=senha,
        id_contato_bling=id_contato_bling,
        nome=nome,
        email=email,
        telefone=telefone
    )
    
    if resultado:
        print(f"Usuário criado com sucesso. ID: {resultado}")
    else:
        print("Falha ao criar usuário.")
    
    return resultado

def testar_buscar_usuario(cpf):
    """
    Testa a busca de um usuário pelo CPF
    """
    print(f"\n=== Testando busca de usuário com CPF {cpf} ===")
    user_manager = UserManager()
    
    usuario = user_manager.get_user_by_cpf(cpf)
    
    if usuario:
        print(f"Usuário encontrado: {usuario.get('nome', 'Sem nome')}")
        print(f"Status: {usuario.get('status', 'desconhecido')}")
        print(f"ID no Bling: {usuario.get('id_contato_bling', 'não definido')}")
    else:
        print("Usuário não encontrado.")
    
    return usuario

def testar_verificar_senha(cpf, senha):
    """
    Testa a verificação de senha
    """
    print(f"\n=== Testando verificação de senha para CPF {cpf} ===")
    user_manager = UserManager()
    
    resultado = user_manager.verify_password(cpf, senha)
    
    if resultado:
        print("Senha correta!")
    else:
        print("Senha incorreta ou usuário não encontrado.")
    
    return resultado

def testar_atualizar_usuario(cpf, dados):
    """
    Testa a atualização de um usuário
    """
    print(f"\n=== Testando atualização de usuário com CPF {cpf} ===")
    user_manager = UserManager()
    
    resultado = user_manager.update_user(cpf, dados)
    
    if resultado:
        print("Usuário atualizado com sucesso.")
        # Busca o usuário atualizado para mostrar os dados
        usuario = user_manager.get_user_by_cpf(cpf)
        if usuario:
            print(f"Dados atualizados: {usuario}")
    else:
        print("Falha ao atualizar usuário.")
    
    return resultado

def testar_desativar_usuario(cpf):
    """
    Testa a desativação de um usuário
    """
    print(f"\n=== Testando desativação de usuário com CPF {cpf} ===")
    user_manager = UserManager()
    
    resultado = user_manager.deactivate_user(cpf)
    
    if resultado:
        print("Usuário desativado com sucesso.")
        # Confirma a desativação
        usuario = user_manager.get_user_by_cpf(cpf)
        if usuario and usuario.get('status') == 'inativo':
            print("Status confirmado como inativo.")
        else:
            print("Erro: Status não foi atualizado corretamente.")
    else:
        print("Falha ao desativar usuário.")
    
    return resultado

def modo_interativo():
    """
    Executa o script em modo interativo
    """
    print("\n=== TESTE DO GERENCIADOR DE USUÁRIOS ===\n")
    
    # Testa a criação da coleção
    testar_criar_colecao()
    
    while True:
        print("\nSelecione uma operação:")
        print("1. Criar usuário")
        print("2. Buscar usuário")
        print("3. Verificar senha")
        print("4. Atualizar usuário")
        print("5. Desativar usuário")
        print("0. Sair")
        
        opcao = input("Opção: ").strip()
        
        if opcao == "0":
            print("Encerrando...")
            break
        
        elif opcao == "1":
            cpf = input("CPF (sem formatação): ").strip()
            senha = input("Senha: ").strip()
            id_contato = input("ID do contato no Bling: ").strip()
            nome = input("Nome (opcional): ").strip() or None
            email = input("Email (opcional): ").strip() or None
            telefone = input("Telefone (opcional): ").strip() or None
            
            testar_criar_usuario(cpf, senha, id_contato, nome, email, telefone)
        
        elif opcao == "2":
            cpf = input("CPF (sem formatação): ").strip()
            testar_buscar_usuario(cpf)
        
        elif opcao == "3":
            cpf = input("CPF (sem formatação): ").strip()
            senha = input("Senha: ").strip()
            testar_verificar_senha(cpf, senha)
        
        elif opcao == "4":
            cpf = input("CPF (sem formatação): ").strip()
            print("Insira os campos a serem atualizados (deixe em branco para manter o valor atual)")
            nome = input("Nome: ").strip() or None
            email = input("Email: ").strip() or None
            telefone = input("Telefone: ").strip() or None
            nova_senha = input("Nova senha (deixe em branco para não alterar): ").strip() or None
            
            dados = {}
            if nome:
                dados['nome'] = nome
            if email:
                dados['email'] = email
            if telefone:
                dados['telefone'] = telefone
            if nova_senha:
                dados['senha'] = nova_senha
            
            if dados:
                testar_atualizar_usuario(cpf, dados)
            else:
                print("Nenhum dado fornecido para atualização.")
        
        elif opcao == "5":
            cpf = input("CPF (sem formatação): ").strip()
            confirma = input(f"Tem certeza que deseja desativar o usuário com CPF {cpf}? (s/n): ").strip().lower()
            
            if confirma == 's':
                testar_desativar_usuario(cpf)
            else:
                print("Operação cancelada.")
        
        else:
            print("Opção inválida.")

def main():
    parser = argparse.ArgumentParser(description='Teste do Gerenciador de Usuários')
    parser.add_argument('--create', action='store_true', help='Criar a coleção de usuários')
    parser.add_argument('--add', action='store_true', help='Adicionar um novo usuário')
    parser.add_argument('--get', action='store_true', help='Buscar um usuário pelo CPF')
    parser.add_argument('--verify', action='store_true', help='Verificar senha de um usuário')
    parser.add_argument('--update', action='store_true', help='Atualizar dados de um usuário')
    parser.add_argument('--deactivate', action='store_true', help='Desativar um usuário')
    
    parser.add_argument('--cpf', help='CPF do usuário (sem formatação)')
    parser.add_argument('--senha', help='Senha do usuário')
    parser.add_argument('--id-contato', help='ID do contato no Bling')
    parser.add_argument('--nome', help='Nome do usuário')
    parser.add_argument('--email', help='Email do usuário')
    parser.add_argument('--telefone', help='Telefone do usuário')
    
    args = parser.parse_args()
    
    # Se nenhum argumento for fornecido, executa em modo interativo
    if len(sys.argv) == 1:
        modo_interativo()
        return
    
    # Executa as operações solicitadas
    if args.create:
        testar_criar_colecao()
    
    if args.add:
        if not args.cpf or not args.senha or not args.id_contato:
            print("Erro: Para adicionar um usuário, forneça --cpf, --senha e --id-contato")
            return
        
        testar_criar_usuario(
            args.cpf,
            args.senha,
            args.id_contato,
            args.nome,
            args.email,
            args.telefone
        )
    
    if args.get:
        if not args.cpf:
            print("Erro: Para buscar um usuário, forneça --cpf")
            return
        
        testar_buscar_usuario(args.cpf)
    
    if args.verify:
        if not args.cpf or not args.senha:
            print("Erro: Para verificar senha, forneça --cpf e --senha")
            return
        
        testar_verificar_senha(args.cpf, args.senha)
    
    if args.update:
        if not args.cpf:
            print("Erro: Para atualizar um usuário, forneça --cpf")
            return
        
        dados = {}
        if args.nome:
            dados['nome'] = args.nome
        if args.email:
            dados['email'] = args.email
        if args.telefone:
            dados['telefone'] = args.telefone
        if args.senha:
            dados['senha'] = args.senha
        
        if dados:
            testar_atualizar_usuario(args.cpf, dados)
        else:
            print("Nenhum dado fornecido para atualização.")
    
    if args.deactivate:
        if not args.cpf:
            print("Erro: Para desativar um usuário, forneça --cpf")
            return
        
        testar_desativar_usuario(args.cpf)

if __name__ == "__main__":
    main() 