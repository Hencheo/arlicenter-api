# Gerenciamento de Usuários no ArliCenter

Este documento descreve a implementação do sistema de gerenciamento de usuários no ArliCenter, que permite aos clientes do Bling acessarem suas próprias informações usando CPF e senha.

## Estrutura da Coleção

A coleção `users` no Firebase Firestore armazena os dados dos usuários com a seguinte estrutura:

```javascript
{
  "cpf": "00000000000",              // CPF sem formatação (chave primária)
  "senha_hash": "bcrypt_hash_here",  // Hash da senha usando bcrypt
  "id_contato_bling": "123456",      // ID do contato no sistema Bling
  "data_cadastro": Timestamp,        // Data de criação do usuário
  "status": "ativo",                // Status (ativo, inativo, bloqueado, etc.)
  "nome": "Nome Completo",           // Nome recuperado do Bling
  "email": "email@exemplo.com",      // Email do usuário
  "telefone": "00000000000",         // Telefone do usuário
  "ultimo_acesso": Timestamp,        // Data do último login
  "perfil": "cliente",               // Tipo de perfil (cliente, administrador)
  "metadata": { ... }                // Metadados adicionais
}
```

## Como Usar o UserManager

### Inicialização

```python
from core.user_manager import UserManager

user_manager = UserManager()
```

### Criar um Novo Usuário

```python
user_manager.create_user(
    cpf="00000000000",
    senha="senha_segura",
    id_contato_bling="123456",
    nome="Nome do Cliente",
    email="cliente@exemplo.com",
    telefone="11999999999"
)
```

### Buscar um Usuário

```python
usuario = user_manager.get_user_by_cpf("00000000000")
if usuario:
    print(f"Nome: {usuario.get('nome')}")
    print(f"Email: {usuario.get('email')}")
    print(f"Status: {usuario.get('status')}")
```

### Verificar Senha

```python
if user_manager.verify_password("00000000000", "senha_para_verificar"):
    print("Senha correta!")
else:
    print("Senha incorreta ou usuário não encontrado.")
```

### Atualizar Dados do Usuário

```python
dados_atualizados = {
    "nome": "Novo Nome",
    "email": "novo_email@exemplo.com",
    "telefone": "11988888888"
}

if user_manager.update_user("00000000000", dados_atualizados):
    print("Usuário atualizado com sucesso.")
else:
    print("Falha ao atualizar usuário.")
```

### Atualizar Senha

```python
if user_manager.update_user("00000000000", {"senha": "nova_senha_segura"}):
    print("Senha atualizada com sucesso.")
else:
    print("Falha ao atualizar senha.")
```

### Desativar um Usuário

```python
if user_manager.deactivate_user("00000000000"):
    print("Usuário desativado com sucesso.")
else:
    print("Falha ao desativar usuário.")
```

## Script de Teste

O script `test_user_manager.py` permite testar todas as funcionalidades do UserManager:

### Modo Interativo

```bash
python test_user_manager.py
```

### Linha de Comando

```bash
# Criar a coleção
python test_user_manager.py --create

# Adicionar um usuário
python test_user_manager.py --add --cpf "00000000000" --senha "senha123" --id-contato "123456" --nome "João Silva"

# Buscar um usuário
python test_user_manager.py --get --cpf "00000000000"

# Verificar senha
python test_user_manager.py --verify --cpf "00000000000" --senha "senha123"

# Atualizar usuário
python test_user_manager.py --update --cpf "00000000000" --nome "João da Silva" --email "joao@exemplo.com"

# Desativar usuário
python test_user_manager.py --deactivate --cpf "00000000000"
```

## Regras de Segurança do Firebase

As regras de segurança do Firestore estão configuradas para garantir que:

1. Usuários só possam acessar seus próprios dados
2. Administradores possam gerenciar todos os usuários
3. Campos sensíveis como `senha_hash` sejam protegidos

As regras completas estão no arquivo `firestore.rules`.

## Próximos Passos

- Implementar endpoints de registro e autenticação de usuários
- Integrar a verificação de CPF com a API do Bling
- Implementar sistema de sessão baseado em JWT 