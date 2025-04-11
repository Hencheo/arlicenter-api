from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        """
        Inicializa o Firebase quando o aplicativo Django é carregado.
        """
        # Importação dentro do método para evitar importações circulares
        try:
            from core.firebase_config import initialize_firebase
            initialize_firebase()
            logger.info("Firebase inicializado com sucesso durante a inicialização do app")
        except Exception as e:
            logger.error(f"Erro ao inicializar Firebase durante startup: {str(e)}")