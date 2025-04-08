# ArliCenter - Backend

Backend do sistema ArliCenter, desenvolvido com Django para gerenciar a integração com o Bling e outras funcionalidades.

## Estrutura do Projeto

```
backend/
├── arlicenter/              # Configurações do projeto Django
│   ├── settings.py          # Configurações do Django
│   ├── urls.py              # URLs principais
│   ├── wsgi.py              # Configuração WSGI para produção
│   └── asgi.py              # Configuração ASGI para produção
├── core/                    # Aplicação principal
│   ├── migrations/          # Migrações do banco de dados
│   ├── views.py             # Implementação das views (incluindo callback Bling)
│   ├── urls.py              # URLs da aplicação
│   └── models.py            # Modelos de dados
├── bling_tokens/            # Diretório para armazenar tokens (não versionado)
├── .gitignore               # Arquivos ignorados pelo Git
├── manage.py                # Script de gerenciamento do Django
├── requirements.txt         # Dependências do projeto
└── README.md                # Este arquivo
```

## Configuração

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente para produção
4. Atualize as credenciais do Bling em `core/views.py`

## Principais Funcionalidades

- Autenticação com Bling via OAuth2
- Endpoint `/auth/callback/` para receber o código de autorização do Bling
- Troca automática do código pelo token de acesso
- Armazenamento seguro do token para futuras requisições

## Desenvolvimento

Para executar o projeto localmente:

```
python manage.py runserver
```

## Deployment

O projeto está configurado para ser implantado no Render em:
https://arlicenter-api.onrender.com 