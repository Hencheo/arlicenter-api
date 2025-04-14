# Tarefas para Implementação do Sistema de Autenticação de Usuários

Este documento detalha as tarefas necessárias para implementar o sistema de autenticação de usuários que permitirá aos clientes do Bling acessarem suas informações usando CPF e senha.

## 1. Criação da Coleção de Usuários no Firebase

### 1.1. Definir Estrutura do Documento de Usuário
- Definir campos obrigatórios (CPF, senha_hash, id_contato_bling, data_cadastro, status)
- Definir campos opcionais (email, telefone, último_acesso, etc.)
- Documentar a estrutura no código

### 1.2. Configurar Regras de Segurança
- Definir regras de acesso para a coleção de usuários
- Implementar regras para garantir que apenas administradores e o próprio usuário possam acessar seus dados
- Testar as regras de segurança

### 1.3. Implementar Função para Criar Usuário
- Criar método para adicionar novos usuários na coleção
- Implementar verificação para evitar duplicidade de CPF
- Adicionar validação de dados antes da criação

### 1.4. Implementar Função para Buscar Usuário por CPF
- Criar método para buscar usuário pelo CPF
- Otimizar a busca com índices adequados
- Implementar tratamento para CPF não encontrado

## 2. Endpoint para Cadastro de Usuários

### 2.1. Criar Rota de Cadastro
- Implementar endpoint `/auth/register/`
- Definir método HTTP (POST) e parâmetros necessários
- Implementar validação dos dados de entrada

### 2.2. Integrar com Verificação de CPF no Bling
- Conectar o endpoint de cadastro com a função `teste_busca_por_cpf` existente
- Extrair o ID do contato no Bling e armazenar junto com os dados do usuário
- Implementar tratamento de erro para CPF não encontrado no Bling

### 2.3. Implementar Criptografia de Senha
- Escolher e implementar algoritmo seguro para hash de senha (bcrypt ou similar)
- Nunca armazenar senhas em texto puro
- Implementar função para verificar senha posteriormente

### 2.4. Resposta de Cadastro
- Definir formato de resposta para cadastro bem-sucedido
- Implementar respostas para diferentes cenários de erro
- Garantir que dados sensíveis não sejam retornados

## 3. Endpoint para Autenticação de Usuários (Login)

### 3.1. Criar Rota de Login
- Implementar endpoint `/auth/login/`
- Definir método HTTP (POST) e parâmetros (CPF, senha)
- Validar dados de entrada

### 3.2. Verificação de Credenciais
- Buscar usuário pelo CPF
- Verificar hash da senha com a senha fornecida
- Implementar proteção contra ataques de força bruta (rate limiting)

### 3.3. Geração de Tokens JWT
- Implementar função para gerar JWT após login bem-sucedido
- Definir payload do token (cpf, id_contato_bling, etc.)
- Configurar tempo de expiração do token

### 3.4. Resposta de Login
- Retornar token JWT para o cliente
- Incluir informações básicas do usuário na resposta
- Atualizar timestamp de último acesso

## 4. Sistema de Sessão/Autenticação

### 4.1. Middleware de Autenticação
- Criar middleware para verificar token JWT em rotas protegidas
- Implementar extração de dados do token e verificação de validade
- Adicionar usuário autenticado ao objeto de requisição

### 4.2. Rotas Protegidas
- Identificar e proteger rotas que requerem autenticação
- Aplicar middleware de autenticação às rotas protegidas
- Implementar níveis de acesso (usuário normal, admin, etc.)

### 4.3. Renovação de Token
- Implementar endpoint para renovar token JWT próximo da expiração
- Verificar validade do token atual antes de renovar
- Manter a sessão dos usuários sem exigir novo login frequente

### 4.4. Logout
- Implementar endpoint para logout
- Adicionar token à lista de tokens inválidos (blacklist)
- Gerenciar expiração de tokens na blacklist

## 5. Vinculação entre Usuários e Contatos do Bling

### 5.1. Armazenamento da Vinculação
- Armazenar ID do contato no Bling no documento do usuário
- Implementar campo para armazenar dados adicionais do contato (nome, email, etc.)
- Definir estratégia para atualização periódica desses dados

### 5.2. Filtro de Dados por Usuário
- Modificar endpoints existentes para filtrar dados pelo ID do contato vinculado ao usuário logado
- Garantir que usuários só acessem seus próprios dados
- Implementar lógica para administradores acessarem dados de múltiplos usuários

### 5.3. Sincronização de Dados
- Implementar função para atualizar dados do usuário quando houver mudanças no Bling
- Definir estratégia de sincronização (sob demanda, periódica, etc.)
- Garantir consistência entre os dados locais e os dados no Bling

## 6. Testes e Documentação

### 6.1. Testes Unitários
- Implementar testes para cada função de autenticação
- Testar fluxos de sucesso e cenários de erro
- Garantir cobertura adequada de código

### 6.2. Testes de Integração
- Testar o fluxo completo de cadastro, login e acesso a dados
- Simular diferentes cenários de uso
- Verificar a integridade das relações entre usuários e dados do Bling

### 6.3. Documentação da API
- Documentar todos os endpoints relacionados à autenticação
- Incluir exemplos de uso e formatos de resposta
- Criar guia de integração para o frontend

### 6.4. Documentação de Segurança
- Documentar as medidas de segurança implementadas
- Incluir instruções para rotação de chaves de segurança
- Definir protocolo para tratamento de incidentes de segurança 