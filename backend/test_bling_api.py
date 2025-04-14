#!/usr/bin/env python
"""
Script para testar chamadas à API do Bling
"""

import requests
import json
import argparse
import os
import time
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def criar_diretorio_tokens():
    """
    Garante que o diretório de tokens exista
    
    Returns:
        str: Caminho do diretório de tokens
    """
    tokens_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bling_tokens')
    
    # Cria o diretório se não existir
    if not os.path.exists(tokens_dir):
        try:
            os.makedirs(tokens_dir)
            print(f"Diretório de tokens criado: {tokens_dir}")
        except Exception as e:
            print(f"Erro ao criar diretório de tokens: {str(e)}")
    
    return tokens_dir

def obter_token_do_arquivo():
    """
    Busca o token de acesso nos arquivos da pasta bling_tokens
    """
    # Procura tokens dentro da pasta bling_tokens do backend
    tokens_dir = criar_diretorio_tokens()
    
    # Verifica primeiro se existe um último token utilizado
    ultimo_token_data, _ = obter_ultimo_token_utilizado()
    if ultimo_token_data and 'access_token' in ultimo_token_data:
        print("Encontrado último token utilizado.")
        # Verifica se o token está expirado
        token_expirado = verificar_expiracao_token(ultimo_token_data)
        if token_expirado:
            print("ATENÇÃO: Este token está expirado!")
        return ultimo_token_data.get('access_token'), ultimo_token_data.get('refresh_token')
    
    # Lista todos os arquivos de token
    arquivos_token = [os.path.join(tokens_dir, f) for f in os.listdir(tokens_dir) if f.startswith('token_') and f.endswith('.json')]
    
    if not arquivos_token:
        print("Nenhum arquivo de token encontrado")
        return obter_token_manual()
    
    # Ordena por data de modificação, mais recente primeiro
    arquivos_token.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Carrega o token mais recente
    with open(arquivos_token[0], 'r') as f:
        token_data = json.load(f)
        
    if 'access_token' not in token_data:
        print("Token inválido, não contém access_token")
        return obter_token_manual()
        
    print(f"Token carregado do arquivo: {arquivos_token[0]}")
    
    # Verifica se o token está expirado
    token_expiracao = token_data.get('data_expiracao')
    if token_expiracao:
        # Converte a string para timestamp
        try:
            token_expiracao = int(token_expiracao)
            agora = int(time.time())
            if token_expiracao < agora:
                print(f"ATENÇÃO: Token expirado! Expirou em: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(token_expiracao))}")
                print("Recomendado renovar o token.")
        except:
            print("Não foi possível verificar a expiração do token.")
    
    # Salva como último token utilizado
    salvar_ultimo_token(token_data)
            
    return token_data['access_token'], token_data.get('refresh_token')

def salvar_ultimo_token(token_data):
    """
    Salva apenas o arquivo ultimo_token.json
    
    Args:
        token_data: Dicionário com os dados do token
    """
    tokens_dir = criar_diretorio_tokens()
    
    # Salva como último token utilizado
    ultimo_token_path = os.path.join(tokens_dir, "ultimo_token.json")
    try:
        with open(ultimo_token_path, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
        print(f"Token salvo como último utilizado em: {ultimo_token_path}")
        return True
    except Exception as e:
        print(f"Erro ao salvar último token: {str(e)}")
        return False

def salvar_token(token_data):
    """
    Salva os dados do token em um arquivo
    
    Args:
        token_data: Dicionário com os dados do token (access_token, refresh_token, etc)
    """
    tokens_dir = criar_diretorio_tokens()
    
    # Nome do arquivo com timestamp
    nome_arquivo = f"token_{int(time.time())}.json"
    caminho_completo = os.path.join(tokens_dir, nome_arquivo)
    
    # Adiciona data de expiração, se não estiver presente
    if 'expires_in' in token_data and 'data_expiracao' not in token_data:
        agora = int(time.time())
        token_data['data_expiracao'] = agora + int(token_data.get('expires_in', 0))
    
    try:
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
        print(f"Token salvo em: {caminho_completo}")
        
        # Salva também como último token utilizado
        salvar_ultimo_token(token_data)
        
        return True
    except Exception as e:
        print(f"Erro ao salvar token: {str(e)}")
        return False

def verificar_expiracao_token(token_data):
    """
    Verifica se um token está expirado
    
    Args:
        token_data: Dicionário com os dados do token
        
    Returns:
        bool: True se o token está expirado, False caso contrário
    """
    expiracao = token_data.get('data_expiracao')
    if not expiracao:
        return False
    
    try:
        agora = int(time.time())
        expiracao = int(expiracao)
        return expiracao < agora
    except:
        return False

def obter_ultimo_token_utilizado():
    """
    Obtém o último token utilizado com sucesso
    
    Returns:
        tuple: (token_data, caminho_arquivo) ou (None, None) se não encontrado
    """
    tokens_dir = criar_diretorio_tokens()
    ultimo_token_path = os.path.join(tokens_dir, "ultimo_token.json")
    
    if not os.path.exists(ultimo_token_path):
        return None, None
    
    try:
        with open(ultimo_token_path, 'r') as f:
            token_data = json.load(f)
            return token_data, ultimo_token_path
    except Exception as e:
        print(f"Erro ao ler último token: {str(e)}")
        return None, None

def renovar_token(refresh_token):
    """
    Renova o token de acesso usando o refresh_token
    
    Args:
        refresh_token: O refresh token para obter um novo access_token
        
    Returns:
        tuple: (access_token, refresh_token) ou (None, None) em caso de erro
    """
    if not refresh_token:
        print("Nenhum refresh_token disponível para renovação")
        return None, None
    
    # Obter credenciais do arquivo .env ou definir valores padrão
    client_id = os.getenv('BLING_CLIENT_ID', 'bed1987ba698d05d51e7e669e9215f552662cecc')
    client_secret = os.getenv('BLING_CLIENT_SECRET', '')
    
    url = "https://api.bling.com.br/Api/v3/oauth/token"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    # Adiciona client_id e client_secret se disponíveis
    if client_id:
        payload["client_id"] = client_id
    if client_secret:
        payload["client_secret"] = client_secret
    
    print(f"Renovando token usando refresh_token: {refresh_token[:10]}...")
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro ao renovar token: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None, None
        
        dados = response.json()
        
        # Salva o novo token
        salvar_token(dados)
        
        return dados.get('access_token'), dados.get('refresh_token')
    except Exception as e:
        print(f"Exceção ao renovar token: {str(e)}")
        return None, None

def obter_token_manual():
    """
    Solicita o token manualmente ao usuário, caso não seja possível obtê-lo automaticamente
    """
    print("\nNão foi possível obter o token automaticamente.")
    print("Você pode solicitar o token acessando a URL:")
    print("https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=bed1987ba698d05d51e7e669e9215f552662cecc&state=teste123&redirect_uri=https://arlicenter-api.onrender.com/auth/callback/")
    print("\nOU pode consultar o token atual através do endpoint:")
    print("https://arlicenter-api.onrender.com/auth/api/token/")
    
    # Solicita o token diretamente ao usuário
    token = input("\nPor favor, cole o token de acesso aqui: ").strip()
    refresh = input("(Opcional) Cole o refresh_token aqui: ").strip()
    
    if token:
        # Remove possíveis espaços e quebras de linha
        token = token.strip()
        # Remove "Bearer " se existir no início do token
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
            
        # Se o usuário forneceu um JSON completo, tenta extrair os tokens
        if token.startswith("{") and token.endswith("}"):
            try:
                token_data = json.loads(token)
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')
                
                if access_token:
                    # Salva o token completo
                    salvar_token(token_data)
                    return access_token, refresh_token
            except:
                # Se falhar ao analisar como JSON, continua com o valor original
                pass
        
        # Cria um objeto de token para salvar
        token_data = {
            "access_token": token,
            "refresh_token": refresh if refresh else None
        }
        
        # Salva o token
        salvar_token(token_data)
                
        return token, refresh
    
    print("Token não fornecido.")
    return None, None

def buscar_contato_por_cpf(token, cpf):
    """
    Busca um contato pelo CPF/CNPJ
    """
    url = f"https://api.bling.com.br/Api/v3/contatos?numeroDocumento={cpf}"
    
    # Verifica se o token já tem o prefixo "Bearer"
    auth_token = token
    if not token.startswith("Bearer "):
        auth_token = f"Bearer {token}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": auth_token,
        "Content-Type": "application/json"
    }
    
    print(f"Buscando contato com CPF/CNPJ: {cpf}")
    print(f"URL: {url}")
    print(f"Authorization: {auth_token[:15]}...")  # Mostra apenas o início do token por segurança
    print(f"Headers completos: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro ao buscar contato: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
        
        dados = response.json()
        return dados
    except Exception as e:
        print(f"Exceção ao fazer a requisição: {str(e)}")
        return None

def buscar_contas_a_receber_por_contato(token, id_contato, situacao=None):
    """
    Busca as contas a receber de um contato específico
    
    Args:
        token: Token de acesso
        id_contato: ID do contato no Bling
        situacao: Situação das contas a receber (1=Em aberto, 2=Recebido, 3=Parcialmente recebido)
    """
    # Monta a URL base
    url = f"https://api.bling.com.br/Api/v3/contas/receber?idContato={id_contato}"
    
    # Adiciona filtro de situação, se especificado
    if situacao:
        url += f"&situacoes[]={situacao}"
    
    # Verifica se o token já tem o prefixo "Bearer"
    auth_token = token
    if not token.startswith("Bearer "):
        auth_token = f"Bearer {token}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": auth_token
    }
    
    print(f"Buscando contas a receber para o contato: {id_contato}")
    if situacao:
        situacoes = {
            "1": "Em aberto",
            "2": "Recebido",
            "3": "Parcialmente recebido"
        }
        print(f"Filtrando por situação: {situacoes.get(str(situacao), situacao)}")
    print(f"URL: {url}")
    print(f"Authorization: {auth_token[:10]}...")  # Mostra apenas o início do token por segurança
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro ao buscar contas a receber: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
        
        dados = response.json()
        return dados
    except Exception as e:
        print(f"Exceção ao fazer a requisição: {str(e)}")
        return None

def fluxo_completo(token, cpf, situacao=None):
    """
    Executa o fluxo completo: busca contato por CPF e depois busca contas a receber
    
    Args:
        token: Token de acesso
        cpf: CPF/CNPJ do contato
        situacao: Situação das contas a receber (1=Em aberto, 2=Recebido, 3=Parcialmente recebido)
    """
    # Busca o contato pelo CPF
    resultado_contato = buscar_contato_por_cpf(token, cpf)
    if not resultado_contato or not resultado_contato.get('data'):
        print(f"Nenhum contato encontrado com o CPF/CNPJ: {cpf}")
        return None
    
    # Extrai o ID do contato
    contato = resultado_contato['data'][0]
    id_contato = contato['id']
    nome_contato = contato['nome']
    
    print(f"Contato encontrado: {nome_contato} (ID: {id_contato})")
    
    # Busca as contas a receber deste contato
    resultado_contas = buscar_contas_a_receber_por_contato(token, id_contato, situacao)
    if not resultado_contas:
        print(f"Erro ao buscar contas a receber para o contato: {id_contato}")
        return None
        
    # Monta o resultado completo
    resultado = {
        "contato": contato,
        "contas_a_receber": resultado_contas.get('data', [])
    }
    
    return resultado

def salvar_resultado(dados, nome_arquivo="resultado_bling.json"):
    """
    Salva o resultado da consulta em um arquivo JSON
    """
    # Definir o diretório para salvar os resultados
    resultados_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultados_bling')
    
    # Cria o diretório se não existir
    if not os.path.exists(resultados_dir):
        os.makedirs(resultados_dir)
    
    # Adiciona timestamp ao nome do arquivo para evitar sobrescrever
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    nome_base = nome_arquivo.rsplit('.', 1)[0]
    extensao = nome_arquivo.rsplit('.', 1)[1] if '.' in nome_arquivo else 'json'
    nome_completo = f"{nome_base}_{timestamp}.{extensao}"
    
    # Caminho completo do arquivo
    caminho_completo = os.path.join(resultados_dir, nome_completo)
    
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    print(f"Resultado salvo no arquivo: {caminho_completo}")

def modo_interativo():
    """
    Executa o script em modo interativo, perguntando o CPF ao usuário
    """
    print("\n=== TESTE DE CONSULTA DE CONTAS A RECEBER DO BLING ===\n")
    
    # Verifica se existe um token utilizado anteriormente
    ultimo_token_data, ultimo_token_path = obter_ultimo_token_utilizado()
    token = None
    refresh_token = None
    
    if ultimo_token_data:
        # Verifica se o token anterior está expirado
        token_expirado = verificar_expiracao_token(ultimo_token_data)
        
        # Formata data de expiração
        if 'data_expiracao' in ultimo_token_data:
            data_expiracao = time.strftime('%d/%m/%Y %H:%M:%S', 
                                            time.localtime(int(ultimo_token_data['data_expiracao'])))
        else:
            data_expiracao = "Desconhecida"
        
        print(f"Encontrado token usado anteriormente.")
        print(f"Data de expiração: {data_expiracao}")
        
        if token_expirado:
            print("ATENÇÃO: Este token está expirado!")
        
        usar_ultimo = input("Deseja usar o último token utilizado? (s/n): ").strip().lower()
        if usar_ultimo == 's':
            token = ultimo_token_data.get('access_token')
            refresh_token = ultimo_token_data.get('refresh_token')
            print("Usando o último token.")
            
            # Se o token estiver expirado, pergunta se deseja renovar
            if token_expirado and refresh_token:
                renovar = input("Token expirado. Deseja tentar renovar com o refresh_token? (s/n): ").strip().lower()
                if renovar == 's':
                    novo_token, novo_refresh = renovar_token(refresh_token)
                    if novo_token:
                        token = novo_token
                        refresh_token = novo_refresh
                        print("Token renovado com sucesso!")
                    else:
                        print("Falha ao renovar o token. Continuando com o token atual.")
    
    # Se não existir um token anterior ou o usuário optar por não usá-lo
    if not token:
        # Opção para inserir token manualmente
        manual = input("Deseja inserir um novo token manualmente? (s/n): ").strip().lower()
        if manual == 's':
            novo_token, novo_refresh = obter_token_manual()
            if novo_token:
                token = novo_token
                refresh_token = novo_refresh
                print("Token atualizado com sucesso!")
        else:
            # Obtém o token dos arquivos salvos
            token, refresh_token = obter_token_do_arquivo()
            
            if not token:
                print("Token de acesso não encontrado. Por favor, autorize a aplicação no Bling primeiro.")
                return
            
            # Opção para renovar o token
            if refresh_token:
                renovar = input("Deseja tentar renovar o token com o refresh_token? (s/n): ").strip().lower()
                if renovar == 's':
                    novo_token, novo_refresh = renovar_token(refresh_token)
                    if novo_token:
                        token = novo_token
                        refresh_token = novo_refresh
                        print("Token renovado com sucesso!")
                    else:
                        print("Falha ao renovar o token. Continuando com o token atual.")
    
    # Solicita o CPF ao usuário
    cpf = input("Digite o CPF/CNPJ sem pontuação: ").strip()
    if not cpf:
        print("CPF/CNPJ não informado. Saindo.")
        return
    
    # Remove pontuações caso o usuário tenha digitado
    cpf = cpf.replace('.', '').replace('-', '').replace('/', '')
    
    # Solicita a situação desejada
    print("\nSituações disponíveis:")
    print("1 - Em aberto")
    print("2 - Recebido")
    print("3 - Parcialmente recebido")
    print("0 - Todas as situações")
    
    situacao = input("Digite o número da situação desejada (padrão: 0): ").strip()
    
    # Converte para None se for 0 ou vazio
    if not situacao or situacao == "0":
        situacao = None
    
    # Executa o fluxo completo
    resultado = fluxo_completo(token, cpf, situacao)
    
    # Exibe um resumo do resultado
    if resultado:
        nome = resultado['contato']['nome']
        qtd_contas = len(resultado['contas_a_receber'])
        print(f"\nResultado para {nome}: {qtd_contas} contas a receber encontradas")
        
        # Mostra resumo das contas
        if qtd_contas > 0:
            print("\nResumo das contas a receber:")
            total_valor = 0
            for i, conta in enumerate(resultado['contas_a_receber']):
                valor = float(conta.get('valor', 0))
                total_valor += valor
                valor_formatado = f"R$ {valor:.2f}".replace('.', ',')
                print(f"{i+1}. Vencimento: {conta.get('vencimento')}, Valor: {valor_formatado}, Situação: {conta.get('situacao')}")
            
            # Exibe o total
            total_formatado = f"R$ {total_valor:.2f}".replace('.', ',')
            print(f"\nTotal: {total_formatado}")
            
            # Pergunta se deseja salvar o resultado
            salvar = input("\nDeseja salvar o resultado em um arquivo? (s/n): ").strip().lower()
            if salvar == 's':
                salvar_resultado(resultado)
        else:
            print("Este contato não possui contas a receber registradas.")
    
    # Pergunta se deseja fazer outra consulta
    outra = input("\nDeseja fazer outra consulta? (s/n): ").strip().lower()
    if outra == 's':
        modo_interativo()

def main():
    parser = argparse.ArgumentParser(description='Teste de chamadas à API do Bling')
    parser.add_argument('--cpf', help='CPF/CNPJ para buscar contato')
    parser.add_argument('--id', help='ID do contato para buscar contas a receber')
    parser.add_argument('--token', help='Token de acesso (opcional, será buscado nos arquivos se não informado)')
    parser.add_argument('--refresh', help='Refresh token para renovar o token de acesso')
    parser.add_argument('--renovar', action='store_true', help='Tentar renovar o token usando o refresh_token')
    parser.add_argument('--situacao', help='Situação das contas a receber (1=Em aberto, 2=Recebido, 3=Parcialmente recebido)')
    parser.add_argument('--salvar', action='store_true', help='Salvar o resultado em um arquivo JSON')
    parser.add_argument('--interativo', action='store_true', help='Executar em modo interativo')
    parser.add_argument('--ultimo-token', action='store_true', help='Usar o último token utilizado')
    
    args = parser.parse_args()
    
    # Verifica se deve executar em modo interativo
    if args.interativo or len(os.sys.argv) == 1:  # Executa interativo se não houver argumentos
        modo_interativo()
        return
    
    # Obtém o token
    token, refresh_token = args.token, args.refresh
    
    # Se foi solicitado usar o último token
    if args.ultimo_token and not token:
        ultimo_token_data, _ = obter_ultimo_token_utilizado()
        if ultimo_token_data:
            token = ultimo_token_data.get('access_token')
            if not refresh_token:
                refresh_token = ultimo_token_data.get('refresh_token')
            print("Usando o último token utilizado.")
            
            # Verifica se o token está expirado
            if verificar_expiracao_token(ultimo_token_data):
                print("ATENÇÃO: O token está expirado!")
                
                # Se tiver refresh_token e argumento de renovação, renova automaticamente
                if refresh_token and args.renovar:
                    novo_token, novo_refresh = renovar_token(refresh_token)
                    if novo_token:
                        token = novo_token
                        refresh_token = novo_refresh
                        print("Token renovado com sucesso!")
    
    # Se não foi fornecido token, tenta obter do arquivo
    if not token:
        token, refresh_token_arquivo = obter_token_do_arquivo()
        # Se não foi fornecido refresh_token como argumento, usa o do arquivo
        if not refresh_token:
            refresh_token = refresh_token_arquivo
    
    # Verifica se deve renovar o token
    if args.renovar and refresh_token:
        novo_token, novo_refresh = renovar_token(refresh_token)
        if novo_token:
            token = novo_token
            refresh_token = novo_refresh
            print("Token renovado com sucesso!")
    
    if not token:
        print("Token de acesso não encontrado")
        return
    
    if args.cpf and args.id:
        print("Por favor, informe apenas CPF/CNPJ ou ID do contato, não ambos")
        return
    
    resultado = None
    
    if args.cpf:
        # Executa o fluxo completo
        resultado = fluxo_completo(token, args.cpf, args.situacao)
    elif args.id:
        # Busca apenas as contas a receber
        resultado = buscar_contas_a_receber_por_contato(token, args.id, args.situacao)
    else:
        print("Informe --cpf ou --id para realizar uma consulta")
        return
    
    # Exibe um resumo do resultado
    if resultado:
        if isinstance(resultado, dict) and 'contato' in resultado:
            # Caso do fluxo completo
            nome = resultado['contato']['nome']
            qtd_contas = len(resultado['contas_a_receber'])
            print(f"\nResultado para {nome}: {qtd_contas} contas a receber encontradas")
            
            # Mostra resumo das contas
            if qtd_contas > 0:
                print("\nResumo das contas a receber:")
                total_valor = 0
                for i, conta in enumerate(resultado['contas_a_receber']):
                    valor = float(conta.get('valor', 0))
                    total_valor += valor
                    valor_formatado = f"R$ {valor:.2f}".replace('.', ',')
                    print(f"{i+1}. Vencimento: {conta.get('vencimento')}, Valor: {valor_formatado}, Situação: {conta.get('situacao')}")
                
                # Exibe o total
                total_formatado = f"R$ {total_valor:.2f}".replace('.', ',')
                print(f"\nTotal: {total_formatado}")
        else:
            # Caso de apenas contas a receber
            qtd_contas = len(resultado.get('data', []))
            print(f"\nResultado: {qtd_contas} contas a receber encontradas")
    
        # Salva o resultado em arquivo se solicitado
        if args.salvar:
            salvar_resultado(resultado)

if __name__ == "__main__":
    main() 