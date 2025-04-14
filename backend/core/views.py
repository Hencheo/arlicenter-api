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

# Importa o gerenciador de notificações
try:
    from core.notification_manager import NotificationManager
except ImportError as e:
    logging.error(f"Erro ao importar NotificationManager: {e}")
    # Classe temporária para evitar falhas completas caso a importação falhe
    class NotificationManager:
        def __init__(self):
            logging.error("NotificationManager não pôde ser carregado corretamente.")
            
        def check_token_expiration(self, token_manager):
            logging.error("Método check_token_expiration chamado, mas NotificationManager não está disponível.")
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
            return JsonResponse({
                "status": "error",
                "error": "Nenhum token ativo encontrado",
                "auth_required": True,
                "authorization_url": generate_authorization_url(request, return_url_only=True)
            }, status=404)
        
        # Verifica a validade do token
        token_valid = True
        if token_data.get("access_token"):
            token_valid = verify_token_validity(token_data.get("access_token"))
        
        # Retorna o token com informações básicas (sem expor access_token completo)
        safe_token_data = {
            "status": "success" if token_valid else "invalid",
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope"),
            "access_token_prefix": token_data.get("access_token", "")[:10] + "..." if token_data.get("access_token") else None,
            "created_at": token_data.get("created_at"),
            "active": token_data.get("active", True),
            "valid": token_valid
        }
        
        # Se o token for inválido, adiciona URL de autorização
        if not token_valid:
            safe_token_data["auth_required"] = True
            safe_token_data["authorization_url"] = generate_authorization_url(request, return_url_only=True)
        
        return JsonResponse(safe_token_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do token: {str(e)}")
        return JsonResponse({"error": f"Erro ao obter informações do token: {str(e)}"}, status=500)

def check_token_status(request):
    """
    Verifica o status do token ativo do Bling.
    Endpoint: /api/token/status/
    """
    try:
        # Inicializa o TokenManager
        token_manager = TokenManager()
        
        # Obtém o token ativo
        token_data = token_manager.get_active_token()
        
        if not token_data:
            return JsonResponse({
                "status": "not_found",
                "valid": False,
                "auth_required": True,
                "authorization_url": generate_authorization_url(request, return_url_only=True)
            })
        
        # Verifica a validade do token
        token_valid = True
        if token_data.get("access_token"):
            token_valid = verify_token_validity(token_data.get("access_token"))
        
        # Se o token não for válido, tenta renovar
        if not token_valid:
            # Tenta renovar o token
            refresh_token = token_data.get("refresh_token")
            token_refreshed = token_manager.refresh_token(refresh_token)
            
            if token_refreshed:
                return JsonResponse({
                    "status": "renewed",
                    "valid": True,
                    "message": "Token foi renovado automaticamente"
                })
            else:
                return JsonResponse({
                    "status": "invalid",
                    "valid": False,
                    "auth_required": True,
                    "message": "Token inválido e não foi possível renová-lo automaticamente",
                    "authorization_url": generate_authorization_url(request, return_url_only=True)
                })
        
        # Se chegou aqui, o token é válido
        return JsonResponse({
            "status": "valid",
            "valid": True,
            "message": "Token ativo e válido"
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do token: {str(e)}")
        return JsonResponse({
            "status": "error",
            "valid": False,
            "error": f"Erro ao verificar status do token: {str(e)}"
        }, status=500)

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
        
        # Verificar a validade do token antes de prosseguir com a requisição principal
        token_valid = verify_token_validity(access_token)
        if not token_valid:
            logger.warning("Token inválido detectado na verificação prévia. Tentando renovar...")
            
            # Tenta renovar o token
            refresh_token = token_data.get("refresh_token")
            token_refreshed = token_manager.refresh_token(refresh_token)
            
            if not token_refreshed:
                # Não foi possível renovar o token
                # Marca o token como inválido no sistema
                token_manager.mark_token_invalid(token_data, error_info)
                
                return JsonResponse({
                    "error": "Token inválido e não foi possível renová-lo. É necessário reautorizar a aplicação.",
                    "auth_required": True,
                    "error_details": error_info
                }, status=401)
            
            # Se conseguiu renovar, pega o novo token
            token_data = token_manager.get_active_token()
            access_token = token_data.get("access_token")
        
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
        
        # Análise detalhada de erros de autenticação
        if response.status_code == 401:
            error_info = {}
            try:
                error_info = response.json()
            except:
                error_info = {"text": response.text}
            
            # Possíveis mensagens de erro de token
            token_errors = [
                "invalid_token",
                "token revoked",
                "token inválido",
                "token expirado",
                "token desativado",
                "acesso negado"
            ]
            
            # Verifica se alguma das mensagens de erro está presente
            error_text = json.dumps(error_info).lower()
            is_token_error = any(error in error_text for error in token_errors)
            
            if is_token_error:
                logger.warning(f"Erro de token detectado: {error_info}")
                
                # Tenta renovar o token
                refresh_token = token_data.get("refresh_token")
                token_refreshed = token_manager.refresh_token(refresh_token)
                
                if not token_refreshed:
                    # Token não pôde ser renovado
                    # Marca o token como inválido no sistema
                    token_manager.mark_token_invalid(token_data, error_info)
                    
                    return JsonResponse({
                        "error": "Token inválido e não foi possível renová-lo. É necessário reautorizar a aplicação.",
                        "auth_required": True,
                        "error_details": error_info
                    }, status=401)
                
                # Se o token foi renovado com sucesso, tenta a requisição novamente
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
                
                # Verifica se a requisição foi bem-sucedida após a renovação
                if response.status_code == 401:
                    logger.error("Falha na requisição mesmo após renovação do token")
                    return JsonResponse({
                        "error": "Falha na autenticação mesmo após renovação do token. É necessário reautorizar a aplicação.",
                        "auth_required": True
                    }, status=401)
        
        # Retorna os dados da API
        return JsonResponse(response.json() if response.content else {}, status=response.status_code)
        
    except Exception as e:
        logger.error(f"Erro ao realizar requisição para a API do Bling: {str(e)}")
        return JsonResponse({"error": f"Erro ao realizar requisição para a API do Bling: {str(e)}"}, status=500)

def verify_token_validity(token):
    """
    Verifica se um token é válido fazendo uma requisição simples à API do Bling
    
    Args:
        token: Token de acesso a ser verificado
        
    Returns:
        bool: True se o token for válido, False caso contrário
    """
    try:
        # Endpoint simples que requer autenticação
        url = "https://api.bling.com.br/Api/v3/usuarios/me"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        logger.info("Verificando validade do token com requisição de teste")
        response = requests.get(url, headers=headers)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            logger.info("Token verificado com sucesso")
            return True
        
        # Se a resposta for 401, o token é inválido
        if response.status_code == 401:
            logger.warning(f"Token inválido: {response.text}")
            return False
        
        # Para outros códigos de status, consideramos o token válido
        # (pode ser um problema específico do endpoint, não do token)
        logger.warning(f"Código de status inesperado na verificação do token: {response.status_code}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar validade do token: {str(e)}")
        # Em caso de erro, consideramos o token válido para evitar falsos negativos
        return True

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

def get_contato_by_id(request, id_contato):
    """
    Endpoint para obter os detalhes completos de um contato pelo ID no Bling
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
        
        # Monta a URL da API para buscar detalhes do contato
        base_url = "https://api.bling.com.br/Api/v3"
        url_contato = f"{base_url}/contatos/{id_contato}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Realizando requisição para obter detalhes do contato: GET {url_contato}")
        response_contato = requests.get(url_contato, headers=headers)
        
        if response_contato.status_code != 200:
            return JsonResponse(response_contato.json() if response_contato.content else {"error": "Erro ao obter detalhes do contato"}, status=response_contato.status_code)
        
        return response_contato.json()
        
    except Exception as e:
        logger.error(f"Erro ao obter detalhes do contato: {str(e)}")
        return {"error": f"Erro ao obter detalhes do contato: {str(e)}"}

def teste_busca_por_cpf_completo(request):
    """
    Endpoint para buscar contatos por CPF e suas contas a receber no Bling.
    Implementa o fluxo completo similar ao script test_bling_api.py.
    """
    cpf = request.GET.get('cpf')
    if not cpf:
        return JsonResponse({"error": "É necessário fornecer um CPF"}, status=400)
    
    # Remove formatação do CPF, mantendo apenas os números
    cpf = ''.join(filter(str.isdigit, cpf))
    
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
        
        # Passo 1: Busca o contato pelo CPF
        contatos_endpoint = f"contatos?numeroDocumento={cpf}"
        base_url = "https://api.bling.com.br/Api/v3"
        url_contatos = f"{base_url}/{contatos_endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Realizando requisição para buscar contato por CPF: GET {url_contatos}")
        response_contatos = requests.get(url_contatos, headers=headers)
        
        if response_contatos.status_code != 200:
            return JsonResponse(response_contatos.json() if response_contatos.content else {"error": "Erro ao buscar contato"}, status=response_contatos.status_code)
        
        dados_contatos = response_contatos.json()
        
        # Verifica se encontrou algum contato
        if not dados_contatos.get('data'):
            return JsonResponse({"data": [], "contas_a_receber": [], "contato_detalhes": {}}, status=200)
        
        # Passo 2: Extrai o ID do contato
        contato = dados_contatos['data'][0]
        id_contato = contato['id']
        
        # Passo 3: Busca os detalhes completos do contato
        detalhes_contato = get_contato_by_id(request, id_contato)
        
        # Verifica se houve erro ao obter detalhes do contato
        if 'error' in detalhes_contato:
            logger.error(f"Erro ao obter detalhes do contato: {detalhes_contato['error']}")
            detalhes_contato = {}
        
        # Passo 4: Busca as contas a receber deste contato
        # Filtra por situação 1 (Em aberto) por padrão
        situacao = request.GET.get('situacao', '1')
        contas_endpoint = f"contas/receber?idContato={id_contato}"
        
        # Adiciona filtro de situação se necessário
        if situacao and situacao != '0':
            contas_endpoint += f"&situacoes[]={situacao}"
        
        url_contas = f"{base_url}/{contas_endpoint.lstrip('/')}"
        
        logger.info(f"Realizando requisição para buscar contas a receber: GET {url_contas}")
        response_contas = requests.get(url_contas, headers=headers)
        
        if response_contas.status_code != 200:
            # Se falhar ao buscar contas, retorna ao menos os dados do contato
            return JsonResponse({
                "data": dados_contatos.get('data', []),
                "contas_a_receber": [],
                "contato_detalhes": detalhes_contato,
                "error_contas": "Erro ao buscar contas a receber"
            }, status=200)
        
        dados_contas = response_contas.json()
        
        # Passo 5: Monta o resultado completo
        resultado_completo = {
            "data": dados_contatos.get('data', []),
            "contas_a_receber": dados_contas.get('data', []),
            "contato_detalhes": detalhes_contato
        }
        
        return JsonResponse(resultado_completo, status=200)
        
    except Exception as e:
        logger.error(f"Erro ao executar fluxo completo de busca por CPF: {str(e)}")
        return JsonResponse({"error": f"Erro ao executar fluxo completo de busca por CPF: {str(e)}"}, status=500)

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

def generate_authorization_url(request, return_url_only=False):
    """
    Gera a URL de autorização para o Bling OAuth.
    
    Args:
        request: Objeto de requisição do Django
        return_url_only: Se True, retorna apenas a URL como string
    
    Returns:
        URL de autorização ou resposta JSON com a URL
    """
    try:
        client_id = settings.BLING_CLIENT_ID
        redirect_uri = settings.BLING_REDIRECT_URI
        
        if not client_id:
            logger.error("Client ID do Bling não configurado")
            if return_url_only:
                return None
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
        
        if return_url_only:
            return auth_url
            
        return JsonResponse({
            "success": True,
            "authorization_url": auth_url
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar URL de autorização: {str(e)}")
        if return_url_only:
            return None
        return JsonResponse({
            "success": False,
            "error": f"Erro ao gerar URL de autorização: {str(e)}"
        }, status=500)

def verify_token_expiration(request):
    """
    Verifica manualmente a expiração do refresh token e envia notificações se necessário.
    Endpoint: /api/token/verify-expiration/
    
    Returns:
        JsonResponse com o status da verificação
    """
    try:
        # Inicializa os gerenciadores
        token_manager = TokenManager()
        notification_manager = NotificationManager()
        
        # Obtém o token ativo para verificar se existe
        token_data = token_manager.get_active_token()
        
        if not token_data:
            return JsonResponse({
                "status": "error",
                "message": "Nenhum token ativo encontrado para verificar",
                "auth_required": True,
                "authorization_url": generate_authorization_url(request, return_url_only=True)
            }, status=404)
        
        # Verifica a expiração do token
        notification_sent = notification_manager.check_token_expiration(token_manager)
        
        # Obtém informações de criação e expiração
        created_at = token_data.get('created_at')
        expires_in = token_data.get('expires_in', 21600)  # access token (6 horas)
        
        # Converte para datetime se for um timestamp do Firestore
        if hasattr(created_at, 'seconds') and hasattr(created_at, 'nanos'):
            # É um timestamp do Firestore
            created_at = datetime.fromtimestamp(created_at.seconds + created_at.nanos/1e9)
        elif isinstance(created_at, str):
            # É uma string ISO (possivelmente de um fallback local)
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.now()
        
        # Calcula a expiração do access token e refresh token
        from datetime import timedelta
        access_expires_at = created_at + timedelta(seconds=expires_in)
        refresh_expires_at = created_at + timedelta(days=30)
        
        # Tempo restante em formato legível
        from django.utils import timezone
        now = timezone.now()
        
        # Se as datas não têm timezone, adiciona
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at)
        
        # Formata tempos restantes
        access_days_remaining = (access_expires_at - now).days if hasattr(access_expires_at, 'days') else None
        refresh_days_remaining = (refresh_expires_at - now).days
        
        result = {
            "status": "success",
            "message": "Verificação de expiração concluída",
            "token_info": {
                "created_at": created_at.isoformat() if created_at else None,
                "access_token_expires_at": access_expires_at.isoformat() if hasattr(access_expires_at, 'isoformat') else None,
                "refresh_token_expires_at": refresh_expires_at.isoformat(),
                "access_token_days_remaining": access_days_remaining,
                "refresh_token_days_remaining": refresh_days_remaining
            },
            "notification_sent": notification_sent
        }
        
        # Se uma notificação foi enviada, adiciona detalhes
        if notification_sent:
            result["notification_info"] = {
                "sent_at": timezone.now().isoformat(),
                "type": "emergency" if refresh_days_remaining <= 1 else "regular",
                "email": settings.EMAIL_DESTINATARIO
            }
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Erro ao verificar expiração do token: {str(e)}")
        return JsonResponse({
            "status": "error",
            "error": f"Erro ao verificar expiração do token: {str(e)}"
        }, status=500)

def run_token_expiration_check(request):
    """
    Executa manualmente a tarefa agendada de verificação de expiração do token.
    Útil para testes em ambientes Windows onde o crontab não funciona.
    Endpoint: /api/token/run-expiration-check/
    
    Returns:
        JsonResponse com o resultado da verificação
    """
    try:
        # Importa a função do cron.py
        from core.cron import check_token_expiration
        
        # Executa a verificação
        check_token_expiration()
        
        return JsonResponse({
            "status": "success",
            "message": "Verificação de expiração executada manualmente com sucesso"
        })
        
    except Exception as e:
        logger.error(f"Erro ao executar verificação manual de expiração: {str(e)}")
        return JsonResponse({
            "status": "error",
            "error": f"Erro ao executar verificação manual: {str(e)}"
        }, status=500)