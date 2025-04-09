#!/usr/bin/env bash
# Script de build para o Render

# Saída de erros
set -o errexit

echo "Instalando dependências Python..."
# Instala dependências Python
pip install -r requirements.txt

# Garantindo que firebase-admin esteja instalado
echo "Garantindo instalação do Firebase Admin SDK..."
pip install firebase-admin==6.2.0 --no-cache-dir

# Verificar e configurar credenciais do Firebase
echo "Configurando credenciais do Firebase..."
mkdir -p credentials
# Se o arquivo de credenciais existe na raiz, copia para a pasta do projeto
if [ -f "../arlicenter-teste-firebase-adminsdk-fbsvc-306d326afc.json" ]; then
    echo "Copiando arquivo de credenciais do Firebase da raiz..."
    cp ../arlicenter-teste-firebase-adminsdk-fbsvc-306d326afc.json firebase-credentials.json
fi

# Coleta arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

# Aplica migrações (descomentar quando houver modelos definidos)
# python manage.py migrate 