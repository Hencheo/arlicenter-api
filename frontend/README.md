# ArliCenter - Frontend

Aplicativo para consulta de CPF e visualização de informações de dívidas.

## Configuração

Antes de executar o aplicativo, é necessário configurar a URL do backend corretamente:

1. Abra o arquivo `config.js`
2. Atualize a variável `API_URL` com a URL do seu backend hospedado no Render
   ```js
   export const API_URL = 'https://arlicenter-api.onrender.com'; // Substitua pela sua URL real
   ```

## Executando o Aplicativo

### Pré-requisitos
- Node.js instalado
- Expo CLI instalado (`npm install -g expo-cli`)
- Expo Go app instalado no seu dispositivo móvel (disponível na App Store ou Google Play)

### Passos para executar

1. Instale as dependências:
   ```
   npm install
   ```

2. Inicie o servidor Expo:
   ```
   npx expo start
   ```

3. Escaneie o QR code com o app Expo Go no seu dispositivo ou pressione:
   - `a` para abrir no emulador Android (requer Android Studio)
   - `i` para abrir no simulador iOS (requer macOS e Xcode)
   - `w` para abrir em um navegador web

## Testando o Aplicativo

1. Após abrir o aplicativo, você verá uma tela com um campo para inserir um CPF
2. Digite um CPF válido (com ou sem formatação)
3. Toque no botão "Consultar"
4. O aplicativo fará uma requisição ao backend e exibirá:
   - Informações do contato (nome, CPF/CNPJ, telefone, email)
   - Lista de contas a receber (valor, data de vencimento, status)

## Funcionalidades

- Consulta de CPF e obtenção de informações de dívidas
- Formatação automática do CPF durante a digitação
- Exibição de informações detalhadas do contato
- Listagem de contas a receber com formatação apropriada para valores e datas
- Tratamento de erros com mensagens amigáveis

## Próximos Passos

- Implementar autenticação de usuários
- Adicionar mais validações
- Melhorar a interface do usuário
- Adicionar funcionalidade de pagamento 