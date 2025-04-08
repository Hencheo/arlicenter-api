#!/usr/bin/env bash
# Script de build para o Render

# Saída de erros
set -o errexit

# Instala dependências Python
pip install -r requirements.txt

# Coleta arquivos estáticos
python manage.py collectstatic --no-input

# Aplica migrações (descomentar quando houver modelos definidos)
# python manage.py migrate 