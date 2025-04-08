from django.shortcuts import render, HttpResponse
import requests
import json
import os
from datetime import datetime
from pathlib import Path
from django.conf import settings

# Create your views here.

def bling_callback(request):
    """
    Recebe o código de autorização do Bling e troca por um token de acesso.
    """
    # Verifica se o código está presente na URL
    code = request.GET.get('code')
    
    if not code:
        return HttpResponse("Código de autorização não encontrado.", status=400)
    
    # Configurações para a troca do código por token
    client_id = settings.BLING_CLIENT_ID
    client_secret = settings.BLING_CLIENT_SECRET
    redirect_uri = settings.BLING_REDIRECT_URI
    grant_type = "authorization_code"
    
    # Verifica se as credenciais estão configuradas
    if not client_id or not client_secret:
        return HttpResponse("Configurações de API do Bling não definidas. Configure as variáveis de ambiente BLING_CLIENT_ID e BLING_CLIENT_SECRET.", status=500)
    
    # Dados para a requisição POST
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": grant_type,
        "redirect_uri": redirect_uri
    }
    
    # Fazendo a requisição para obter o token
    try:
        response = requests.post("https://www.bling.com.br/Api/v3/oauth/token", data=data)
        response.raise_for_status()  # Lança exceção para respostas de erro HTTP
        
        # Extrai os dados do token
        token_data = response.json()
        
        # Cria o diretório para armazenar os tokens se não existir
        tokens_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens'))
        tokens_dir.mkdir(exist_ok=True)
        
        # Salva o token em um arquivo JSON
        filename = tokens_dir / f"token_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(token_data, f, indent=4)
        
        return HttpResponse("Token obtido com sucesso e salvo com segurança.")
        
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"Erro ao obter o token: {str(e)}", status=500)
