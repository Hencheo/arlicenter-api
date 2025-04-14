# Tratamento de Tokens Inválidos no Frontend

Este documento descreve como o frontend lida com situações onde os tokens de acesso à API do Bling são invalidados ou revogados.

## Problema

O Bling pode revogar tokens de acesso por questões de segurança, especialmente quando ocorrem alterações nas permissões ou configurações de autorização. Quando isso acontece, o token armazenado no nosso sistema se torna inválido, mesmo que ainda não tenha expirado pelo tempo normal.

## Solução Implementada

O frontend foi preparado para lidar com essas situações de forma elegante, seguindo estas etapas:

### 1. Verificação Proativa

Antes de realizar uma consulta à API do Bling, o aplicativo verifica o status do token usando o endpoint `/api/token/status/`. Esta verificação proativa permite identificar tokens inválidos antes mesmo de tentar usá-los.

### 2. Tratamento de Erros de Autenticação

Se o token for inválido ou tiver sido revogado, o aplicativo:

1. Exibe uma notificação informando o usuário sobre a necessidade de reautorização
2. Oferece opções para o usuário:
   - Cancelar a operação
   - Prosseguir com a reautorização

### 3. Fluxo de Reautorização

Se o usuário optar por reautorizar o acesso:

1. O aplicativo abre o navegador com a URL de autorização do Bling
2. O usuário realiza a autenticação diretamente no site do Bling
3. Após a autorização bem-sucedida, o usuário retorna ao aplicativo e pode tentar a operação novamente

### 4. Tratamento de Respostas 401

Além da verificação proativa, o aplicativo também detecta respostas com código 401 (Unauthorized) durante as requisições regulares e aplica o mesmo fluxo de reautorização.

## Como Funciona

O código em `App.js` implementa duas camadas de proteção:

1. **Verificação prévia**: Antes de cada operação, verifica o status do token
```javascript
const tokenStatusResponse = await axios.get(`${API_URL}${ENDPOINTS.TOKEN_STATUS}`);
```

2. **Captura de erros 401**: Trata especificamente respostas de erro relacionadas à autenticação
```javascript
if (err.response && err.response.status === 401) {
  // Lógica de tratamento de erro de autenticação
}
```

## Benefícios

Esta abordagem oferece uma experiência de usuário mais suave:

- Evita falhas inesperadas quando tokens são revogados
- Fornece mensagens claras sobre o que está acontecendo
- Oferece um caminho direto para resolver o problema
- Mantém a integridade da segurança do sistema

## Manutenção

Se for necessário alterar as permissões da API no Bling ou realizar outras configurações de segurança, o aplicativo continuará funcionando corretamente, orientando os usuários no processo de reautorização quando necessário. 