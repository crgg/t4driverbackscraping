# slack_comunication/slack_client.py
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackClient:
    """
    Cliente para enviar mensajes a Slack usando la API oficial de Slack.
    
    Esta clase maneja la comunicación con Slack a través de:
    - Bot Token (recomendado): Usando la API oficial de Slack
    - Webhook URL (alternativo): Usando Incoming Webhooks
    
    Attributes:
        bot_token (str): Token del bot de Slack (xoxb-...)
        webhook_url (str): URL del webhook entrante (opcional)
        channel (str): Canal por defecto para enviar mensajes
        enabled (bool): Si las notificaciones están habilitadas
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        webhook_url: Optional[str] = None,
        channel: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Inicializa el cliente de Slack.
        
        Args:
            bot_token: Token del bot de Slack (xoxb-...)
            webhook_url: URL del webhook de Slack
            channel: Canal por defecto (#nombre-canal)
            enabled: Si las notificaciones están habilitadas
        """
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.channel = channel or os.getenv("SLACK_CHANNEL", "#errores-criticos")
        self.enabled = enabled and os.getenv("SLACK_ENABLED", "1") == "1"
        
        # Cliente de Slack (importación lazy)
        self._slack_client = None
        
        # Validar configuración
        self._validar_configuracion()
    
    def _validar_configuracion(self) -> None:
        """
        Valida que la configuración sea correcta.
        
        Raises:
            ValueError: Si la configuración es inválida
        """
        if not self.enabled:
            logger.info("ℹ️ Notificaciones de Slack deshabilitadas (SLACK_ENABLED != 1)")
            return
        
        if not self.bot_token and not self.webhook_url:
            logger.warning(
                "⚠️ No se configuró SLACK_BOT_TOKEN ni SLACK_WEBHOOK_URL. "
                "Las notificaciones de Slack estarán deshabilitadas."
            )
            self.enabled = False
            return
        
        if self.bot_token:
            logger.info(f"✓ Cliente de Slack configurado con Bot Token para canal {self.channel}")
        elif self.webhook_url:
            logger.info(f"✓ Cliente de Slack configurado con Webhook URL para canal {self.channel}")
    
    def _get_slack_client(self):
        """
        Obtiene el cliente de Slack (lazy loading).
        
        Returns:
            WebClient: Cliente de Slack
        """
        if self._slack_client is None and self.bot_token:
            try:
                from slack_sdk import WebClient
                from slack_sdk.errors import SlackApiError
                
                self._slack_client = WebClient(token=self.bot_token)
                logger.debug("✓ WebClient de Slack inicializado")
            except ImportError as e:
                logger.error(
                    f"❌ Error al importar slack_sdk: {e}. "
                    "Instala con: pip install slack-sdk"
                )
                raise
        
        return self._slack_client
    
    def enviar_mensaje(
        self,
        texto: str,
        channel: Optional[str] = None,
        bloques: Optional[list] = None
    ) -> bool:
        """
        Envía un mensaje a Slack.
        
        Args:
            texto: Texto del mensaje (usado como fallback si hay bloques)
            channel: Canal específico (opcional, usa el por defecto si no se provee)
            bloques: Lista de bloques con formato rico (opcional)
        
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        if not self.enabled:
            logger.debug("ℹ️ Notificaciones de Slack deshabilitadas, no se envía mensaje")
            return False
        
        canal_destino = channel or self.channel
        
        try:
            # Intentar con Bot Token primero
            if self.bot_token:
                return self._enviar_con_bot_token(texto, canal_destino, bloques)
            
            # Fallback a Webhook
            elif self.webhook_url:
                return self._enviar_con_webhook(texto, bloques)
            
            else:
                logger.error("❌ No hay método de envío configurado")
                return False
        
        except Exception as e:
            logger.error(
                f"❌ Error inesperado al enviar mensaje a Slack: {e}",
                exc_info=True
            )
            return False
    
    def _enviar_con_bot_token(
        self,
        texto: str,
        channel: str,
        bloques: Optional[list] = None
    ) -> bool:
        """
        Envía mensaje usando Bot Token.
        
        Args:
            texto: Texto del mensaje
            channel: Canal destino
            bloques: Bloques con formato rico
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Importar dependencias necesarias
            from slack_sdk.errors import SlackApiError
            
            client = self._get_slack_client()
            
            # Preparar payload
            payload = {
                "channel": channel,
                "text": texto,
            }
            
            if bloques:
                payload["blocks"] = bloques
            
            # Enviar mensaje
            response = client.chat_postMessage(**payload)
            
            if response["ok"]:
                logger.info(f"✅ Mensaje enviado a Slack ({channel})")
                return True
            else:
                logger.error(f"❌ Error en respuesta de Slack: {response}")
                return False
        
        except ImportError as e:
            logger.error(
                f"❌ No se pudo importar slack_sdk: {e}. "
                "Instala con: pip install slack-sdk",
                exc_info=True
            )
            return False
        
        except Exception as e:
            # Intentar capturar SlackApiError si está disponible
            try:
                from slack_sdk.errors import SlackApiError
                if isinstance(e, SlackApiError):
                    logger.error(
                        f"❌ Error de API de Slack: {e.response.get('error', 'Unknown')}",
                        exc_info=True
                    )
                    return False
            except ImportError:
                pass
            
            # Error genérico
            logger.error(
                f"❌ Error al enviar mensaje con Bot Token: {e}",
                exc_info=True
            )
            return False
    
    def _enviar_con_webhook(
        self,
        texto: str,
        bloques: Optional[list] = None
    ) -> bool:
        """
        Envía mensaje usando Webhook URL.
        
        Args:
            texto: Texto del mensaje
            bloques: Bloques con formato rico
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            import requests
            
            # Preparar payload
            payload: Dict[str, Any] = {"text": texto}
            
            if bloques:
                payload["blocks"] = bloques
            
            # Enviar request
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Mensaje enviado a Slack (webhook)")
                return True
            else:
                logger.error(
                    f"❌ Error al enviar webhook: "
                    f"status={response.status_code}, body={response.text}"
                )
                return False
        
        except Exception as e:
            logger.error(
                f"❌ Error al enviar mensaje con Webhook: {e}",
                exc_info=True
            )
            return False
    
    def test_conexion(self) -> bool:
        """
        Prueba la conexión con Slack.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        if not self.enabled:
            logger.warning("⚠️ Slack deshabilitado, no se puede probar conexión")
            return False
        
        try:
            if self.bot_token:
                from slack_sdk.errors import SlackApiError
                
                client = self._get_slack_client()
                response = client.auth_test()
                
                if response["ok"]:
                    logger.info(
                        f"✅ Conexión exitosa a Slack. "
                        f"Bot: {response.get('user')}, "
                        f"Team: {response.get('team')}"
                    )
                    return True
                else:
                    logger.error(f"❌ Error en test de autenticación: {response}")
                    return False
            
            elif self.webhook_url:
                # Para webhooks, intentamos enviar un mensaje de prueba
                return self.enviar_mensaje("🔧 Test de conexión exitoso")
            
            else:
                logger.error("❌ No hay método configurado para probar conexión")
                return False
        
        except Exception as e:
            logger.error(
                f"❌ Error al probar conexión con Slack: {e}",
                exc_info=True
            )
            return False
