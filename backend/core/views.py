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

# Importa o gerenciador de usuários
try:
    from core.user_manager import UserManager
except ImportError as e:
    logging.error(f"Erro ao importar UserManager: {e}")
    # Classe temporária para evitar falhas completas caso a importação falhe
    class UserManager:
        def __init__(self):
            logging.error("UserManager não pôde ser carregado corretamente.")
            
        def get_user_by_cpf(self, cpf):
            logging.error("Método get_user_by_cpf chamado, mas UserManager não está disponível.")
            return None
            
        def verify_password(self, cpf, senha):
            logging.error("Método verify_password chamado, mas UserManager não está disponível.")
            return False

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
        request: Objeto de requisição do Django
        endpoint: Endpoint da API do Bling (sem a URL base)
        method: Método HTTP (GET, POST, etc)
    
    Returns:
        JsonResponse com os dados da API ou mensagem de erro
    """
    try:
        # Inicializa o TokenManager
        token_manager = TokenManager()
        
        # Obtém o token ativo
        token_data = token_manager.get_active_token()
        
        if not token_data:
            return JsonResponse({"error": "Nenhum token ativo encontrado"}, status=401)
        
        # Obtém o access_token
        access_token = token_data.get("access_token")
        
        if not access_token:
            return JsonResponse({"error": "Token inválido"}, status=401)
        
        # Formato correto da URL base da API do Bling V3 
        base_url = "https://api.bling.com.br/Api/v3"
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        # Cabeçalhos para a requisição
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Realiza a requisição
        logger.info(f"Realizando requisição para a API do Bling: {method} {url}")
        response = None
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json.loads(request.body) if request.body else {})
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=json.loads(request.body) if request.body else {})
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return JsonResponse({"error": f"Método HTTP não suportado: {method}"}, status=400)
        
        # Verifica se o token expirou
        if response.status_code == 401 and "invalid_token" in response.text:
            logger.warning("Token expirado ou inválido. Tentando renovar...")
            
            # Tenta renovar o token
            token_refreshed = token_manager.refresh_token(token_data.get("refresh_token"))
            
            # Se o token foi renovado com sucesso, tenta a requisição novamente
            if token_refreshed:
                # Obtém o novo token
                new_token_data = token_manager.get_active_token()
                new_access_token = new_token_data.get("access_token")
                
                # Atualiza o cabeçalho com o novo token
                headers["Authorization"] = f"Bearer {new_access_token}"
                
                # Tenta a requisição novamente
                logger.info(f"Tentando novamente com token renovado: {method} {url}")
                
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers, json=json.loads(request.body) if request.body else {})
                elif method.upper() == "PUT":
                    response = requests.put(url, headers=headers, json=json.loads(request.body) if request.body else {})
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers)
            else:
                return JsonResponse({"error": "Falha ao renovar token expirado"}, status=401)
        
        # Retorna os dados da API
        return JsonResponse(response.json() if response.content else {}, status=response.status_code)
        
    except Exception as e:
        logger.error(f"Erro ao realizar requisição para a API do Bling: {str(e)}")
        return JsonResponse({"error": f"Erro ao realizar requisição para a API do Bling: {str(e)}"}, status=500)

def get_bling_produtos(request):
    """Endpoint para obter produtos do Bling."""
    return bling_api_request(request, "produtos")

def get_bling_pedidos(request):
    """Endpoint para obter pedidos do Bling."""
    return bling_api_request(request, "pedidos")

def get_bling_contatos(request):
    """Endpoint para obter contatos do Bling."""
    return bling_api_request(request, "contatos")

def user_login(request):
    """
    Endpoint para autenticação de usuários por CPF e senha
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        cpf = data.get("cpf")
        senha = data.get("senha")
        
        if not cpf or not senha:
            return JsonResponse({"error": "CPF e senha são obrigatórios"}, status=400)
        
        # Remove formatação do CPF, mantendo apenas os números
        cpf = ''.join(filter(str.isdigit, cpf))
        
        # Inicializa o UserManager
        user_manager = UserManager()
        
        # Verifica se a senha está correta
        if user_manager.verify_password(cpf, senha):
            # Obtém os dados do usuário
            user_data = user_manager.get_user_by_cpf(cpf)
            
            if not user_data:
                return JsonResponse({"error": "Erro ao obter dados do usuário"}, status=500)
            
            # Remove dados sensíveis
            safe_user_data = {
                "cpf": user_data.get("cpf"),
                "nome": user_data.get("nome"),
                "email": user_data.get("email"),
                "telefone": user_data.get("telefone"),
                "status": user_data.get("status"),
                "perfil": user_data.get("perfil"),
                "id_contato_bling": user_data.get("id_contato_bling")
            }
            
            return JsonResponse({
                "success": True,
                "message": "Login realizado com sucesso",
                "user": safe_user_data
            })
        else:
            return JsonResponse({
                "success": False,
                "error": "CPF ou senha incorretos"
            }, status=401)
            
    except Exception as e:
        logger.error(f"Erro ao processar login: {str(e)}")
        return JsonResponse({"error": f"Erro ao processar login: {str(e)}"}, status=500)

def teste_busca_por_cpf(request):
    """
    Endpoint para testar a busca de contatos por CPF no Bling
    """
    cpf = request.GET.get('cpf')
    if not cpf:
        return JsonResponse({"error": "É necessário fornecer um CPF"}, status=400)
    
    # Remove formatação do CPF, mantendo apenas os números
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # Monta a URL da API com o filtro por CPF
    endpoint = f"contatos?numeroDocumento={cpf}"
    
    # Faz a requisição
    return bling_api_request(request, endpoint)

def delete_all_tokens(request):
    """
    Exclui todos os tokens armazenados no Firestore.
    Endpoint: /api/tokens/delete-all/
    
    Retorna:
        JsonResponse com o número de tokens excluídos ou mensagem de erro
    """
    try:
        # Inicializa o TokenManager
        token_manager = TokenManager()
        
        # Exclui todos os tokens
        deleted_count = token_manager.delete_all_tokens()
        
        return JsonResponse({
            "success": True,
            "message": f"{deleted_count} tokens foram excluídos com sucesso."
        })
        
    except Exception as e:
        logger.error(f"Erro ao excluir tokens: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"Erro ao excluir tokens: {str(e)}"
        }, status=500)

def generate_authorization_url(request):
    """
    Gera a URL de autorização para o Bling OAuth.
    Endpoint: /api/auth/generate-url/
    
    Returns:
        JsonResponse com a URL de autorização
    """
    try:
        client_id = settings.BLING_CLIENT_ID
        redirect_uri = settings.BLING_REDIRECT_URI
        
        if not client_id:
            logger.error("Client ID do Bling não configurado")
            return JsonResponse({
                "success": False,
                "error": "Client ID do Bling não configurado"
            }, status=500)
        
        # Gera um state aleatório para segurança
        import random
        import string
        state = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        # Constrói a URL de autorização
        auth_url = f"https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id={client_id}&state={state}&redirect_uri={redirect_uri}"
        
        return JsonResponse({
            "success": True,
            "authorization_url": auth_url
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar URL de autorização: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"Erro ao gerar URL de autorização: {str(e)}"
        }, status=500)