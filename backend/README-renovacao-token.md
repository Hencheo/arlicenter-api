# Renovação Automática de Token do Bling

Esta documentação descreve como a renovação automática de tokens do Bling foi implementada no backend do ArliCenter.

## Visão Geral

O sistema OAuth2 do Bling utiliza tokens de acesso que expiram após um determinado período (geralmente 6 horas). Para evitar que os usuários precisem reautenticar constantemente, implementamos um mecanismo de renovação automática de tokens usando o `refresh_token`.

## Implementação

A renovação automática de tokens está implementada em duas partes principais:

### 1. `TokenManager.refresh_token()`

Esta função no arquivo `core/token_manager.py` é responsável por renovar tokens expirados:

- Recebe um token expirado como entrada
- Extrai o `refresh_token` do token expirado
- Faz uma requisição POST para o endpoint de token do Bling (`api.bling.com.br/Api/v3/oauth/token`)
- Desativa tokens antigos no Firestore
- Salva o novo token no Firestore e como fallback local
- Retorna o novo token se bem-sucedido, ou o token original em caso de erro

### 2. Integração com as requisições à API

A função `bling_api_request()` no arquivo `core/views.py` foi adaptada para:

- Detectar respostas 401 (Unauthorized) da API do Bling
- Quando uma resposta 401 é recebida, tentar renovar o token automaticamente
- Se a renovação for bem-sucedida, repetir a requisição original com o novo token
- Registrar logs detalhados do processo de renovação

## Fluxo de Renovação

1. O `TokenManager.get_active_token()` verifica proativamente se o token está próximo de expirar (10 minutos antes)
2. Se o token estiver próximo de expirar, `refresh_token()` é chamado para renová-lo
3. Se uma requisição falhar com um erro 401, o sistema também tenta renovar o token e repetir a requisição

## Tratamento de Erros

- Se a renovação falhar, o sistema mantém o token original e registra o erro
- As requisições continuam funcionando se o token original ainda for válido
- Logs detalhados são registrados para facilitar a depuração de problemas

## Considerações de Segurança

- Os tokens são armazenados de forma segura no Firestore
- Tokens antigos são desativados quando novos são criados
- Backups locais são criados como fallback em caso de problemas com o Firestore

## Exemplos de Uso

A renovação de token é transparente para os usuários da API:

```python
# A renovação de token é tratada automaticamente
response = bling_api_request(request, "contatos", "GET")
```

## Troubleshooting

Se ocorrerem problemas com a renovação de token:

1. Verifique os logs do servidor para mensagens de erro detalhadas
2. Confirme que o `refresh_token` ainda é válido (eles eventualmente também expiram)
3. Verifique se as credenciais do cliente (client_id, client_secret) estão configuradas corretamente
4. Em último caso, reautentique o usuário para obter um novo conjunto de tokens 