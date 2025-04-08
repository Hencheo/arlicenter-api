from django.shortcuts import render, HttpResponse
import requests
import json
import os
import logging
import base64
from datetime import datetime
from pathlib import Path
from django.conf import settings

# Configurar logger
logger = logging.getLogger(__name__)

def index(request):
    """
    Página inicial simples para o ArliCenter API.
    """
    return HttpResponse("ArliCenter API está rodando. Use /auth/callback/ para integração com Bling.")

def bling_callback(request):
    """
    Recebe o código de autorização do Bling e troca por um token de acesso.
    """
    try:
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
            logger.error("Credenciais do Bling não configuradas")
            return HttpResponse("Configurações de API do Bling não definidas. Configure as variáveis de ambiente BLING_CLIENT_ID e BLING_CLIENT_SECRET.", status=500)
        
        # Dados para a requisição POST - não incluindo client_id e client_secret no corpo
        data = {
            "code": code,
            "grant_type": grant_type,
            "redirect_uri": redirect_uri
        }
        
        # Preparando a autenticação Basic
        auth_str = f"{client_id}:{client_secret}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Headers para a requisição com autenticação Basic
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        # Log das informações (exceto secrets)
        logger.info(f"Realizando requisição OAuth para o Bling com redirect_uri={redirect_uri}")
        logger.info(f"Código recebido: {code}")
        logger.info(f"Usando autenticação Basic nos cabeçalhos")
        
        # Fazendo a requisição para obter o token
        try:
            # Usando autenticação Basic nos cabeçalhos em vez de credenciais no corpo
            response = requests.post(
                "https://www.bling.com.br/Api/v3/oauth/token", 
                data=data,
                headers=headers
            )
            
            # Log da resposta para diagnóstico
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Headers: {response.headers}")
            
            if response.status_code != 200:
                logger.error(f"Resposta de erro do Bling: {response.text}")
                return HttpResponse(f"Erro ao obter o token: {response.status_code} - {response.text}", status=500)
            
            # Extrai os dados do token
            token_data = response.json()
            
            # Tenta criar diretório temporário caso o diretório padrão falhe
            try:
                tokens_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens'))
                tokens_dir.mkdir(exist_ok=True)
            except Exception as dir_error:
                logger.warning(f"Não foi possível criar o diretório bling_tokens: {str(dir_error)}")
                tokens_dir = Path(os.path.join('/tmp', 'bling_tokens'))
                tokens_dir.mkdir(exist_ok=True)
            
            # Salva o token em um arquivo JSON
            filename = tokens_dir / f"token_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(token_data, f, indent=4)
            
            logger.info("Token obtido e salvo com sucesso")
            return HttpResponse("Token obtido com sucesso e salvo com segurança.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para o Bling: {str(e)}")
            # Log adicional para ajudar no diagnóstico
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalhes da resposta: {e.response.text}")
            
            return HttpResponse(f"Erro ao obter o token: {str(e)}", status=500)
    
    except Exception as e:
        logger.exception("Erro não tratado no callback do Bling")
        return HttpResponse(f"Erro interno do servidor: {str(e)}", status=500)
