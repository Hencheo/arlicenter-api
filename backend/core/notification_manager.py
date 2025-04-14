"""
Módulo para gerenciar notificações sobre a expiração de tokens do Bling.
Responsável por enviar emails e SMS para alertar sobre a necessidade de renovação de tokens.
"""

import logging
import datetime
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests
import json
import os
from pathlib import Path

# Configurar logger
logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Classe para gerenciar notificações de expiração de tokens.
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de notificações
        """
        self.notification_log_dir = Path(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notification_logs'))
        self.notification_log_dir.mkdir(exist_ok=True)
        self.notification_log_file = self.notification_log_dir / 'token_notifications.json'
        self.email_destinatario = settings.EMAIL_DESTINATARIO
        self.telefone_destinatario = settings.TELEFONE_DESTINATARIO
        self.url_authorization = settings.URL_AUTHORIZATION
        logger.info("NotificationManager inicializado com sucesso")
    
    def check_token_expiration(self, token_manager):
        """
        Verifica a expiração do refresh token e envia notificações quando necessário
        
        Args:
            token_manager: Instância do TokenManager para verificar os tokens
            
        Returns:
            bool: True se alguma notificação foi enviada, False caso contrário
        """
        try:
            # Obtém o token ativo
            token_data = token_manager.get_active_token()
            
            if not token_data or 'refresh_token' not in token_data:
                # Sem token ativo ou sem refresh token, já precisamos renovar
                logger.warning("Nenhum token ativo ou refresh token encontrado. Enviando notificação de emergência.")
                self.send_notification(is_emergency=True)
                return True
            
            # Calcular quando o refresh token expira (criação + 30 dias)
            created_at = token_data.get('created_at')
            
            # Converte para datetime se for um timestamp do Firestore
            if hasattr(created_at, 'seconds') and hasattr(created_at, 'nanos'):
                # É um timestamp do Firestore
                created_at = datetime.datetime.fromtimestamp(created_at.seconds + created_at.nanos/1e9)
            elif isinstance(created_at, str):
                # É uma string ISO (possivelmente de um fallback local)
                try:
                    created_at = datetime.datetime.fromisoformat(created_at)
                except ValueError:
                    logger.error(f"Formato de data inválido: {created_at}")
                    return False
            elif created_at is None:
                logger.error("Data de criação do token não encontrada")
                return False
            
            # Se a data não tem timezone, adiciona
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            
            # O refresh token expira em 30 dias
            expires_at = created_at + timedelta(days=30)
            
            # Tempo restante
            days_remaining = (expires_at - timezone.now()).days
            
            logger.info(f"Token criado em {created_at}, expira em {expires_at}. Dias restantes: {days_remaining}")
            
            # Verifica se já enviamos uma notificação recentemente
            last_notification = self._get_last_notification()
            current_date = timezone.now().date()
            
            # Regras para enviar notificações
            if days_remaining <= 1:
                # Notificação de emergência
                if not last_notification or \
                   last_notification.get('type') != 'emergency' or \
                   (datetime.datetime.fromisoformat(last_notification.get('date')).date() != current_date):
                    logger.info("Enviando notificação de emergência para renovação de token")
                    self.send_notification(is_emergency=True)
                    return True
            elif days_remaining <= 5:
                # Notificação normal
                if not last_notification or \
                   (datetime.datetime.fromisoformat(last_notification.get('date')).date() < current_date - timedelta(days=1)):
                    logger.info("Enviando notificação regular para renovação de token")
                    self.send_notification(is_emergency=False)
                    return True
            
            return False
                
        except Exception as e:
            logger.error(f"Erro ao verificar expiração do token: {str(e)}")
            return False
    
    def send_notification(self, is_emergency=False):
        """
        Envia notificações por email e, se for emergência, também por SMS
        
        Args:
            is_emergency (bool): Se verdadeiro, indica que é uma notificação urgente
            
        Returns:
            bool: True se a notificação foi enviada com sucesso, False caso contrário
        """
        try:
            # Obtém a URL de autorização
            auth_url = self._get_authorization_url()
            
            if not auth_url:
                logger.error("Não foi possível obter a URL de autorização")
                return False
            
            # Configura o assunto com base na urgência
            subject = "🚨 URGENTE: Renovação de acesso ao Bling necessária" if is_emergency else "⚠️ Renovação de acesso ao Bling em breve"
            
            # Corpo do email com HTML mais elaborado e melhor formatado
            if is_emergency:
                message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Renovação de Token Urgente</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            margin: 0;
                            padding: 0;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background-color: #FF0000;
                            color: white;
                            padding: 10px 20px;
                            text-align: center;
                            border-radius: 5px 5px 0 0;
                        }}
                        .content {{
                            padding: 20px;
                            border: 1px solid #ddd;
                            border-top: none;
                            border-radius: 0 0 5px 5px;
                        }}
                        .btn {{
                            display: inline-block;
                            background-color: #FF0000;
                            color: white;
                            padding: 12px 25px;
                            text-decoration: none;
                            border-radius: 4px;
                            font-weight: bold;
                            margin: 20px 0;
                        }}
                        .footer {{
                            margin-top: 20px;
                            text-align: center;
                            font-size: 12px;
                            color: #777;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚨 AÇÃO URGENTE NECESSÁRIA</h1>
                        </div>
                        <div class="content">
                            <p><strong>O token de acesso ao Bling está prestes a expirar em menos de 24 horas.</strong></p>
                            <p>Se não for renovado, o sistema ArliCenter <strong>deixará de funcionar</strong> e você não conseguirá acessar informações de clientes e pagamentos!</p>
                            
                            <p style="text-align: center;"><a href="{auth_url}" class="btn">RENOVAR ACESSO AGORA</a></p>
                            
                            <h3>Como renovar seu acesso:</h3>
                            <ol>
                                <li>Clique no botão acima</li>
                                <li>Faça login com suas credenciais do Bling</li>
                                <li>Clique em "Autorizar"</li>
                                <li>Você receberá uma confirmação que o acesso foi renovado</li>
                            </ol>
                            
                            <p><strong>Em caso de dúvidas, entre em contato com o suporte técnico imediatamente.</strong></p>
                        </div>
                        <div class="footer">
                            <p>Esta é uma mensagem automática do sistema ArliCenter. Por favor, não responda a este email.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            else:
                message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Renovação de Token do Bling</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            margin: 0;
                            padding: 0;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background-color: #4CAF50;
                            color: white;
                            padding: 10px 20px;
                            text-align: center;
                            border-radius: 5px 5px 0 0;
                        }}
                        .content {{
                            padding: 20px;
                            border: 1px solid #ddd;
                            border-top: none;
                            border-radius: 0 0 5px 5px;
                        }}
                        .btn {{
                            display: inline-block;
                            background-color: #4CAF50;
                            color: white;
                            padding: 12px 25px;
                            text-decoration: none;
                            border-radius: 4px;
                            font-weight: bold;
                            margin: 20px 0;
                        }}
                        .footer {{
                            margin-top: 20px;
                            text-align: center;
                            font-size: 12px;
                            color: #777;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>⚠️ Renovação Planejada</h1>
                        </div>
                        <div class="content">
                            <p>O token de acesso ao Bling expirará nos próximos dias. Para garantir a continuidade do serviço sem interrupções, recomendamos que a renovação seja feita o quanto antes.</p>
                            
                            <p style="text-align: center;"><a href="{auth_url}" class="btn">Renovar Acesso ao Bling</a></p>
                            
                            <h3>Como renovar seu acesso:</h3>
                            <ol>
                                <li>Clique no botão acima</li>
                                <li>Faça login com suas credenciais do Bling</li>
                                <li>Clique em "Autorizar"</li>
                                <li>Você receberá uma confirmação que o acesso foi renovado</li>
                            </ol>
                        </div>
                        <div class="footer">
                            <p>Esta é uma mensagem automática do sistema ArliCenter. Por favor, não responda a este email.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            # Versão texto simples para clientes de email que não suportam HTML
            plain_message = strip_tags(message)
            
            # Envia o email
            email_sent = send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email_destinatario],
                html_message=message,
                fail_silently=False,
            )
            
            # Se for emergência, enviar também SMS
            sms_sent = False
            if is_emergency:
                sms_content = f"URGENTE: Token do Bling expira em breve. Acesse {auth_url} para renovar o acesso ao ArliCenter."
                sms_sent = self._send_sms(sms_content, self.telefone_destinatario)
            
            # Registra que a notificação foi enviada
            self._record_notification_sent(
                notification_type="emergency" if is_emergency else "regular",
                email_sent=bool(email_sent),
                sms_sent=sms_sent
            )
            
            logger.info(f"Notificação {'de emergência' if is_emergency else 'regular'} enviada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {str(e)}")
            return False
    
    def _get_authorization_url(self):
        """
        Obtém a URL de autorização do Bling
        
        Returns:
            str: URL de autorização ou None em caso de erro
        """
        try:
            # Primeiro, tenta usar a URL configurada nas variáveis de ambiente
            if self.url_authorization:
                # Se a URL já é a URL completa, retorna ela mesma
                if "https://" in self.url_authorization:
                    # Faz uma requisição para obter a URL real de autorização
                    response = requests.get(self.url_authorization)
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("authorization_url")
                    else:
                        logger.error(f"Erro ao obter URL de autorização: {response.status_code} - {response.text}")
                # Se é apenas um endpoint, completa com o domínio
                return self.url_authorization
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter URL de autorização: {str(e)}")
            return None
    
    def _record_notification_sent(self, notification_type, email_sent, sms_sent):
        """
        Registra que uma notificação foi enviada
        
        Args:
            notification_type (str): Tipo de notificação ('emergency' ou 'regular')
            email_sent (bool): Se o email foi enviado com sucesso
            sms_sent (bool): Se o SMS foi enviado com sucesso
        """
        try:
            # Cria o objeto de log
            log_entry = {
                "date": timezone.now().isoformat(),
                "type": notification_type,
                "email_sent": email_sent,
                "sms_sent": sms_sent
            }
            
            # Lê o log existente ou cria um novo
            log_data = []
            if self.notification_log_file.exists():
                with open(self.notification_log_file, 'r') as f:
                    try:
                        log_data = json.load(f)
                    except json.JSONDecodeError:
                        log_data = []
            
            # Adiciona a nova entrada
            log_data.append(log_entry)
            
            # Salva o log atualizado
            with open(self.notification_log_file, 'w') as f:
                json.dump(log_data, f, indent=4)
                
            logger.info(f"Registro de notificação salvo com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao registrar notificação: {str(e)}")
    
    def _get_last_notification(self):
        """
        Obtém a última notificação enviada
        
        Returns:
            dict: Dados da última notificação ou None se não houver
        """
        try:
            if not self.notification_log_file.exists():
                return None
                
            with open(self.notification_log_file, 'r') as f:
                try:
                    log_data = json.load(f)
                    if not log_data:
                        return None
                    
                    # Retorna a entrada mais recente
                    return sorted(log_data, key=lambda x: x.get('date'), reverse=True)[0]
                except json.JSONDecodeError:
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao obter última notificação: {str(e)}")
            return None
    
    def check_token_renewed(self, token_manager):
        """
        Verifica se o token foi renovado após o envio de uma notificação
        
        Args:
            token_manager: Instância do TokenManager para verificar os tokens
            
        Returns:
            bool: True se o token foi renovado, False caso contrário
        """
        try:
            # Obtém a última notificação
            last_notification = self._get_last_notification()
            if not last_notification:
                return False
                
            # Obtém o token ativo
            token_data = token_manager.get_active_token()
            if not token_data:
                return False
                
            # Obtém a data de criação do token
            created_at = token_data.get('created_at')
            
            # Converte para datetime se for um timestamp do Firestore
            if hasattr(created_at, 'seconds') and hasattr(created_at, 'nanos'):
                # É um timestamp do Firestore
                created_at = datetime.datetime.fromtimestamp(created_at.seconds + created_at.nanos/1e9)
            elif isinstance(created_at, str):
                # É uma string ISO (possivelmente de um fallback local)
                try:
                    created_at = datetime.datetime.fromisoformat(created_at)
                except ValueError:
                    logger.error(f"Formato de data inválido: {created_at}")
                    return False
            elif created_at is None:
                logger.error("Data de criação do token não encontrada")
                return False
            
            # Se a data não tem timezone, adiciona
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
                
            # Data da última notificação
            notification_date = datetime.datetime.fromisoformat(last_notification.get('date'))
            
            # Verifica se o token foi criado após a última notificação
            if created_at > notification_date:
                logger.info(f"Token renovado com sucesso após notificação")
                # Registra que o token foi renovado com sucesso após notificação
                self._record_token_renewal(token_data.get('id', 'unknown'), notification_date)
                # Cancela o ciclo de notificação
                self._cancel_notification_cycle()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar renovação do token: {str(e)}")
            return False
            
    def _record_token_renewal(self, token_id, notification_date):
        """
        Registra a renovação bem-sucedida de um token após notificação
        
        Args:
            token_id (str): Identificador do token renovado
            notification_date (datetime): Data da notificação que levou à renovação
        """
        try:
            # Cria o objeto de registro
            renewal_entry = {
                "date": timezone.now().isoformat(),
                "token_id": token_id,
                "notification_date": notification_date.isoformat(),
                "success": True
            }
            
            # Define o caminho do arquivo de registro
            renewal_log_file = self.notification_log_dir / 'token_renewals.json'
            
            # Lê o registro existente ou cria um novo
            renewal_data = []
            if renewal_log_file.exists():
                with open(renewal_log_file, 'r') as f:
                    try:
                        renewal_data = json.load(f)
                    except json.JSONDecodeError:
                        renewal_data = []
            
            # Adiciona a nova entrada
            renewal_data.append(renewal_entry)
            
            # Salva o registro atualizado
            with open(renewal_log_file, 'w') as f:
                json.dump(renewal_data, f, indent=4)
                
            logger.info(f"Registro de renovação de token salvo com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao registrar renovação de token: {str(e)}")
    
    def _cancel_notification_cycle(self):
        """
        Cancela o ciclo atual de notificações após uma renovação bem-sucedida
        """
        try:
            # Cria uma marca de cancelamento para indicar que o ciclo atual foi resolvido
            cancellation_entry = {
                "date": timezone.now().isoformat(),
                "action": "cancel_cycle",
                "reason": "token_renewed"
            }
            
            # Define o caminho do arquivo de controle de ciclo
            cycle_control_file = self.notification_log_dir / 'notification_cycle_control.json'
            
            # Lê o controle existente ou cria um novo
            cycle_data = []
            if cycle_control_file.exists():
                with open(cycle_control_file, 'r') as f:
                    try:
                        cycle_data = json.load(f)
                    except json.JSONDecodeError:
                        cycle_data = []
            
            # Adiciona a entrada de cancelamento
            cycle_data.append(cancellation_entry)
            
            # Salva o controle atualizado
            with open(cycle_control_file, 'w') as f:
                json.dump(cycle_data, f, indent=4)
                
            logger.info(f"Ciclo de notificação cancelado após renovação bem-sucedida")
            
        except Exception as e:
            logger.error(f"Erro ao cancelar ciclo de notificação: {str(e)}")
    
    def is_notification_cycle_active(self):
        """
        Verifica se existe um ciclo de notificação ativo
        
        Returns:
            bool: True se houver um ciclo ativo, False caso contrário
        """
        try:
            # Define o caminho do arquivo de controle de ciclo
            cycle_control_file = self.notification_log_dir / 'notification_cycle_control.json'
            
            # Se o arquivo não existe, não há ciclo ativo
            if not cycle_control_file.exists():
                return False
                
            # Lê o controle existente
            with open(cycle_control_file, 'r') as f:
                try:
                    cycle_data = json.load(f)
                except json.JSONDecodeError:
                    return False
            
            # Se não há dados, não há ciclo ativo
            if not cycle_data:
                return False
            
            # Verifica se o último registro é um cancelamento
            last_entry = cycle_data[-1]
            if last_entry.get('action') == 'cancel_cycle':
                # O ciclo foi cancelado
                return False
            
            # Verifica se há uma notificação recente (nas últimas 24 horas)
            last_notification = self._get_last_notification()
            if not last_notification:
                return False
                
            # Converte a data da última notificação para datetime
            notification_date = datetime.datetime.fromisoformat(last_notification.get('date'))
            
            # Verifica se a notificação foi enviada nas últimas 24 horas
            time_since_notification = timezone.now() - notification_date
            if time_since_notification.days < 1:
                # Há uma notificação recente e o ciclo não foi cancelado
                return True
                
            return False
                
        except Exception as e:
            logger.error(f"Erro ao verificar ciclo de notificação: {str(e)}")
            return False
            
    def get_notification_status(self):
        """
        Retorna o status atual das notificações
        
        Returns:
            dict: Status das notificações, incluindo ciclo ativo, última notificação, etc.
        """
        try:
            # Status inicial
            status = {
                "cycle_active": self.is_notification_cycle_active(),
                "last_notification": None,
                "renewal_status": None
            }
            
            # Obtém a última notificação
            last_notification = self._get_last_notification()
            if last_notification:
                status["last_notification"] = {
                    "date": last_notification.get('date'),
                    "type": last_notification.get('type'),
                    "email_sent": last_notification.get('email_sent', False),
                    "sms_sent": last_notification.get('sms_sent', False)
                }
            
            # Verifica se houve renovação após a última notificação
            renewal_log_file = self.notification_log_dir / 'token_renewals.json'
            if renewal_log_file.exists():
                try:
                    with open(renewal_log_file, 'r') as f:
                        renewal_data = json.load(f)
                        if renewal_data:
                            # Obtém a última renovação
                            last_renewal = renewal_data[-1]
                            status["renewal_status"] = {
                                "date": last_renewal.get('date'),
                                "success": last_renewal.get('success', False),
                                "token_id": last_renewal.get('token_id')
                            }
                except:
                    pass
            
            return status
            
        except Exception as e:
            logger.error(f"Erro ao obter status de notificação: {str(e)}")
            return {"error": str(e)}
    
    def _send_sms(self, message, phone_number):
        """
        Envia uma mensagem SMS usando o Twilio
        
        Args:
            message (str): Conteúdo da mensagem SMS
            phone_number (str): Número de telefone do destinatário no formato internacional
            
        Returns:
            bool: True se o SMS foi enviado com sucesso, False caso contrário
        """
        try:
            # Verifica se as credenciais do Twilio estão configuradas
            twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
            
            if not twilio_account_sid or not twilio_auth_token or not twilio_phone_number:
                logger.warning("Credenciais do Twilio não configuradas. SMS não será enviado.")
                return False
            
            # Verifica se o número de telefone está no formato correto
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
            
            try:
                # Tenta importar a biblioteca Twilio
                from twilio.rest import Client
                
                # Inicializa o cliente Twilio
                client = Client(twilio_account_sid, twilio_auth_token)
                
                # Envia o SMS
                sms = client.messages.create(
                    body=message,
                    from_=twilio_phone_number,
                    to=phone_number
                )
                
                logger.info(f"SMS enviado com sucesso: {sms.sid}")
                return True
                
            except ImportError:
                # Caso a biblioteca Twilio não esteja instalada, faz uma requisição HTTP direta
                # Esta é uma implementação alternativa caso a biblioteca não esteja disponível
                logger.warning("Biblioteca Twilio não instalada. Tentando método alternativo.")
                
                # URL da API do Twilio
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
                
                # Prepara os dados para a requisição
                data = {
                    'To': phone_number,
                    'From': twilio_phone_number,
                    'Body': message
                }
                
                # Prepara a autenticação
                auth = (twilio_account_sid, twilio_auth_token)
                
                # Faz a requisição
                response = requests.post(url, data=data, auth=auth)
                
                # Verifica se a requisição foi bem-sucedida
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info("SMS enviado com sucesso via API HTTP")
                    return True
                else:
                    logger.error(f"Erro ao enviar SMS via API HTTP: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Erro ao enviar SMS: {str(e)}")
            return False 