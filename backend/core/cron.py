"""
Módulo para definir tarefas agendadas (cron jobs) para o sistema.
"""

import logging
from core.token_manager import TokenManager
from core.notification_manager import NotificationManager

# Configurar logger
logger = logging.getLogger(__name__)

def check_token_expiration():
    """
    Verifica a expiração do refresh token e envia notificações quando necessário.
    Esta função é executada diariamente às 8:00 através do django-crontab.
    """
    try:
        # Inicializa os gerenciadores
        token_manager = TokenManager()
        notification_manager = NotificationManager()
        
        # Verifica a expiração do token
        notification_sent = notification_manager.check_token_expiration(token_manager)
        
        if notification_sent:
            logger.info("Notificação de expiração de token enviada com sucesso")
        else:
            # Verifica se o token foi renovado após o envio de uma notificação
            token_renewed = notification_manager.check_token_renewed(token_manager)
            if token_renewed:
                logger.info("Token renovado com sucesso após notificação")
        
        logger.info("Verificação de expiração de token concluída com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao verificar expiração do token: {str(e)}") 