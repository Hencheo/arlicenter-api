# ArliCenter

Sistema de integração com a API do Bling para gerenciamento de ordem de serviços e faturamento.

## Estrutura do Projeto

O projeto está organizado em dois componentes principais:

```
arlicenter/
├── frontend/           # Aplicativo React Native
│   ├── assets/         # Recursos (imagens, fontes)
│   ├── components/     # Componentes reutilizáveis
│   ├── screens/        # Telas da aplicação
│   ├── services/       # Integrações com APIs
│   └── ...
│
├── backend/            # API Django
│   ├── arlicenter/     # Configurações do projeto
│   ├── core/           # Aplicação principal
│   │   ├── views.py    # Lógica da API
│   │   ├── urls.py     # Rotas da API
│   │   └── ...
│   ├── bling_tokens/   # Armazenamento seguro de tokens
│   └── ...
└── ...
```

## Funcionalidades

- Autenticação OAuth2 com o Bling
- Gerenciamento de ordens de serviço
- Integração com sistema de pagamentos
- Emissão de notas fiscais

## Primeiros Passos

### Backend (Django)

1. Navegue até o diretório backend:
   ```
   cd backend
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` baseado no `.env.example`
   - Adicione suas credenciais do Bling

4. Execute o servidor:
   ```
   python manage.py runserver
   ```

### Frontend (React Native)

*Em desenvolvimento*

## Deployment

- Backend: https://arlicenter-api.onrender.com
- Frontend: *Em breve*

## Licença

[MIT](LICENSE) 