from django.shortcuts import render, HttpResponse
import requests
import json
import os
import logging
import base64
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse

# Importação com tratamento de erro
try:
    from core.token_manager import TokenManager
except ImportError as e:
    logging.error(f"Erro ao importar TokenManager: {e}")
    # Classe temporária para evitar falhas completas caso a importação falhe
    class TokenManager:
        def __init__(self):
            logging.error("TokenManager não pôde ser carregado corretamente.")
            
        def create_token_document(self, token_data):
            logging.error("Método create_token_document chamado, mas TokenManager não está disponível.")
            return None
            
        def get_active_token(self):
            logging.error("Método get_active_token chamado, mas TokenManager não está disponível.")
            return None

# Configurar logger
logger = logging.getLogger(__name__)

def index(request):
    """
    Página inicial simples para o ArliCenter API.
    """
    return HttpResponse("ArliCenter API está rodando. Use /auth/callback/ para integração com Bling.")

def build_auth_headers(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    auth_bytes = auth_str.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    return headers

def get_bling_token(code, client_id, client_secret, redirect_uri):
    url = "https://www.bling.com.br/Api/v3/oauth/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    headers = build_auth_headers(client_id, client_secret)
    logger.info(f"Realizando requisição OAuth para o Bling com redirect_uri={redirect_uri}")
    logger.info(f"Código recebido: {code}")
    logger.info(f"Usando autenticação Basic nos cabeçalhos")
    response = requests.post(url, data=data, headers=headers)
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response Headers: {response.headers}")
    if response.status_code != 200:
        logger.error(f"Resposta de erro do Bling: {response.text}")
        raise Exception(f"Erro ao obter o token: {response.status_code} - {response.text}")
    return response.json()

def save_token_to_firebase(token_data):
    """
    Salva o token no Firebase Firestore.
    
    Args:
        token_data (dict): Dados do token recebido da API do Bling.
    
    Returns:
        bool: True se o token foi salvo com sucesso, False caso contrário.
    """
    try:
        # Inicializa o gerenciador de tokens
        token_manager = TokenManager()
        
        # Cria um novo documento com os dados do token
        doc_id = token_manager.create_token_document(token_data)
        
        if not doc_id:
            logger.error("Falha ao salvar token no Firebase")
            return False
            
        logger.info(f"Token salvo com sucesso no Firebase. ID do documento: {doc_id}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao salvar token no Firebase: {str(e)}")
        return False

# Manter função antiga para compatibilidade temporária
def save_token_to_file(token_data):
    try:
        tokens_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bling_tokens'))
        tokens_dir.mkdir(exist_ok=True)
    except Exception as dir_error:
        logger.warning(f"Não foi possível criar o diretório bling_tokens: {str(dir_error)}")
        tokens_dir = Path(os.path.join('/tmp', 'bling_tokens'))
        tokens_dir.mkdir(exist_ok=True)
    filename = tokens_dir / f"token_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(token_data, f, indent=4)
    logger.info("Token obtido e salvo com sucesso no arquivo local")

def bling_callback(request):
    """
    Recebe o código de autorização do Bling e troca por um token de acesso.
    Salva o token no Firebase Firestore.
    """
    try:
        code = request.GET.get('code')
        if not code:
            logger.warning("Código de autorização não encontrado na requisição")
            return HttpResponse("Código de autorização não encontrado.", status=400)

        client_id = settings.BLING_CLIENT_ID
        client_secret = settings.BLING_CLIENT_SECRET
        redirect_uri = settings.BLING_REDIRECT_URI

        if not client_id or not client_secret:
            logger.error("Credenciais do Bling não configuradas")
            return HttpResponse("Configurações de API do Bling não definidas. Configure as variáveis de ambiente BLING_CLIENT_ID e BLING_CLIENT_SECRET.", status=500)

        try:
            # Obtém o token do Bling
            token_data = get_bling_token(code, client_id, client_secret, redirect_uri)
            
            # Inicializa o TokenManager para salvar o token no Firebase
            token_manager = TokenManager()
            token_id = token_manager.create_token_document(token_data)
            
            # Como backup, também salva em arquivo local
            try:
                save_token_to_file(token_data)
            except Exception as file_error:
                logger.warning(f"Não foi possível salvar o token em arquivo local: {str(file_error)}")
            
            # Verifica se o token foi salvo com sucesso
            if token_id:
                logger.info(f"Token obtido e salvo com sucesso. ID: {token_id}")
                return HttpResponse("Token obtido com sucesso e salvo com segurança. Você já pode fechar esta janela e utilizar a API.")
            else:
                logger.error("Falha ao salvar o token no Firebase, mas foi salvo em arquivo local")
                return HttpResponse("Token obtido com sucesso, mas houve falha ao salvá-lo. Foi salvo em arquivo local como backup.", status=500)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para o Bling: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalhes da resposta: {e.response.text}")
            return HttpResponse(f"Erro ao obter o token: {str(e)}", status=500)
        except Exception as e:
            logger.error(f"Erro ao obter ou salvar o token: {str(e)}")
            return HttpResponse(f"Erro ao obter ou salvar o token: {str(e)}", status=500)

    except Exception as e:
        logger.exception("Erro não tratado no callback do Bling")
        return HttpResponse(f"Erro interno do servidor: {str(e)}", status=500)

def get_bling_token_info(request):
    """
    Retorna as informações do token ativo do Bling.
    Endpoint: /api/token/
    """
    try:
        # Inicializa o TokenManager
        token_manager = TokenManager()
        
        # Obtém o token ativo
        token_data = token_manager.get_active_token()
        
        if not token_data:
            return JsonResponse({"error": "Nenhum token ativo encontrado"}, status=404)
        
        # Retorna o token com informações básicas (sem expor access_token completo)
        safe_token_data = {
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope"),
            "access_token_prefix": token_data.get("access_token", "")[:10] + "..." if token_data.get("access_token") else None,
            "created_at": token_data.get("created_at"),
            "active": token_data.get("active", True),
        }
        
        return JsonResponse(safe_token_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do token: {str(e)}")
        return JsonResponse({"error": f"Erro ao obter informações do token: {str(e)}"}, status=500)

def bling_api_request(request, endpoint, method="GET"):
    """
    Realiza uma requisição para a API do Bling utilizando o token ativo.
    
    Args:
        request: Requisição HTTP
        endpoint: Endpoint da API do Bling (sem a URL base)
        method: Método HTTP (GET, POST, PUT, DELETE)
    """
    try:
        # Inicializa o TokenManager
        token_manager = TokenManager()
        
        # Obtém o token ativo
        token_data = token_manager.get_active_token()
        
        if not token_data or "access_token" not in token_data:
            return JsonResponse({"error": "Token não disponível"}, status=401)
        
        # Monta a URL da API
        base_url = "https://www.bling.com.br/Api/v3"
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        # Prepara os headers
        headers = {
            "Authorization": f"Bearer {token_data['access_token']}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Dados da requisição (para POST, PUT)
        data = request.body.decode('utf-8') if request.body else None
        
        # Log da requisição
        logger.info(f"Realizando requisição {method} para {url}")
        
        # Realiza a requisição
        if method == "GET":
            response = requests.get(url, headers=headers, params=request.GET.dict())
        elif method == "POST":
            response = requests.post(url, headers=headers, data=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, data=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return JsonResponse({"error": f"Método HTTP não suportado: {method}"}, status=400)
        
        # Log da resposta
        logger.info(f"Resposta da API do Bling: {response.status_code}")
        
        # Tenta converter para JSON
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"text": response.text}
        
        # Retorna a resposta
        return JsonResponse(response_data, status=response.status_code, safe=False)
        
    except Exception as e:
        logger.error(f"Erro ao realizar requisição para a API do Bling: {str(e)}")
        return JsonResponse({"error": f"Erro ao realizar requisição para a API do Bling: {str(e)}"}, status=500)

def get_bling_produtos(request):
    """
    Obtém a lista de produtos do Bling.
    Endpoint: /api/produtos/
    """
    return bling_api_request(request, "produtos", "GET")

def get_bling_pedidos(request):
    """
    Obtém a lista de pedidos do Bling.
    Endpoint: /api/pedidos/
    """
    return bling_api_request(request, "pedidos", "GET")

def get_bling_contatos(request):
    """
    Obtém a lista de contatos do Bling.
    Endpoint: /api/contatos/
    """
    return bling_api_request(request, "contatos", "GET")

# Função de teste para buscar contato por CPF e suas contas a receber
def teste_busca_por_cpf(request):
    """
    Testa a busca de contato por CPF e depois busca as contas a receber deste contato.
    Endpoint: /api/teste/cpf/?cpf=NUMERO_CPF
    """
    try:
        # Obtém o CPF da requisição
        cpf = request.GET.get('cpf')
        if not cpf:
            return JsonResponse({"error": "CPF não fornecido"}, status=400)
        
        logger.info(f"Testando busca por CPF: {cpf}")
        
        # 1. Busca o contato pelo CPF
        contatos_response = bling_api_request(request, f"contatos?numeroDocumento={cpf}", "GET")
        
        # Se a resposta não for um JsonResponse, retorna ela diretamente
        if not isinstance(contatos_response, JsonResponse):
            return contatos_response
        
        # Converte a resposta para dicionário Python
        contatos_data = json.loads(contatos_response.content)
        
        # Verifica se encontrou contatos
        if not contatos_data or not contatos_data.get('data'):
            return JsonResponse({"error": "Nenhum contato encontrado com este CPF"}, status=404)
        
        # Extrai o ID do primeiro contato encontrado
        contato_id = contatos_data['data'][0]['id']
        logger.info(f"Contato encontrado com ID: {contato_id}")
        
        # 2. Busca as contas a receber deste contato
        contas_response = bling_api_request(request, f"contas/receber?idContato={contato_id}", "GET")
        
        # Se a resposta não for um JsonResponse, retorna ela diretamente
        if not isinstance(contas_response, JsonResponse):
            return contas_response
        
        # Converte a resposta para dicionário Python
        contas_data = json.loads(contas_response.content)
        
        # Monta a resposta com os dados do contato e suas contas
        resultado = {
            "contato": contatos_data['data'][0],
            "contas_a_receber": contas_data.get('data', [])
        }
        
        return JsonResponse(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao testar busca por CPF: {str(e)}")
        return JsonResponse({"error": f"Erro ao testar busca por CPF: {str(e)}"}, status=500)
