# sms/twilio_client.py
import os
import logging
import time
from typing import Optional

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


class TwilioSMSClient:
    """
    Cliente para enviar SMS usando Twilio.
    
    Maneja la autenticación, validación y envío de mensajes SMS
    con logging detallado y manejo de errores.
    """
    
    def __init__(self):
        """
        Inicializa el cliente de Twilio con credenciales del .env
        
        Variables de entorno requeridas:
            - TWILIO_ACCOUNT_SID: Account SID de Twilio
            - TWILIO_AUTH_TOKEN: Auth Token de Twilio
            - TWILIO_FROM_NUMBER: Número de teléfono origen (formato: +1XXXXXXXXXX)
            - TWILIO_TO_NUMBER: Número de teléfono destino (formato: +56XXXXXXXXX)
            - TWILIO_ENABLED: 1 para habilitar, 0 para deshabilitar (opcional, default: 1)
        """
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.to_number = os.getenv("TWILIO_TO_NUMBER")
        self.enabled = os.getenv("TWILIO_ENABLED", "1") == "1"
        
        self._client = None
        self._validate_credentials()
    
    def _validate_credentials(self) -> bool:
        """
        Valida que todas las credenciales necesarias estén configuradas.
        
        Returns:
            bool: True si las credenciales son válidas
        """
        missing = []
        
        if not self.account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not self.auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not self.from_number:
            missing.append("TWILIO_FROM_NUMBER")
        if not self.to_number:
            missing.append("TWILIO_TO_NUMBER")
        
        if missing:
            logger.warning(
                f"❌ Credenciales de Twilio faltantes: {', '.join(missing)}. "
                "SMS deshabilitado."
            )
            self.enabled = False
            return False
        
        return True
    
    def _get_client(self):
        """
        Obtiene o crea el cliente de Twilio (lazy loading).
        
        Returns:
            twilio.rest.Client: Cliente de Twilio
        """
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("✓ Cliente de Twilio inicializado correctamente")
            except ImportError:
                logger.error(
                    "❌ No se pudo importar twilio. "
                    "Instala con: pip install twilio"
                )
                self.enabled = False
                raise
            except Exception as e:
                logger.error(f"❌ Error al inicializar cliente de Twilio: {e}")
                self.enabled = False
                raise
        
        return self._client
    
    def enviar_sms(self, mensaje: str, numero_destino: Optional[str] = None) -> bool:
        """
        Envía un SMS usando Twilio.
        
        Args:
            mensaje: Contenido del SMS (máx 160 caracteres recomendado)
            numero_destino: Número destino (opcional, usa TWILIO_TO_NUMBER por defecto)
        
        Returns:
            bool: True si el SMS se envió correctamente, False en caso contrario
        """
        if not self.enabled:
            logger.warning("⚠️ SMS deshabilitado (TWILIO_ENABLED=0 o credenciales faltantes)")
            return False
        
        destino = numero_destino or self.to_number
        
        # Validar longitud del mensaje
        if len(mensaje) > 160:
            logger.warning(
                f"⚠️ Mensaje SMS muy largo ({len(mensaje)} chars). "
                "Twilio puede dividirlo en múltiples SMS."
            )
        
        # Reintentos con backoff exponencial para manejar errores transitorios
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            try:
                client = self._get_client()
                
                # FIX: Hacer un fetch de la cuenta antes de enviar el mensaje
                # Esto resuelve un bug/quirk en la librería Twilio donde
                # messages.create() falla con HTTP 404 si no se ha hecho
                # ninguna otra operación API primero.
                # Esto solo afecta a algunas cuentas Trial.
                # El fetch es OBLIGATORIO, no opcional.
                account = client.api.accounts(self.account_sid).fetch()
                logger.debug(f"✓ Cliente Twilio inicializado: {account.friendly_name}")
                # Pequeño delay para asegurar que el cliente está listo
                time.sleep(0.5)
                
                logger.info(f"📤 Enviando SMS a {destino}... (intento {intento}/{max_intentos})")
                logger.debug(f"Mensaje: {mensaje}")
                
                message = client.messages.create(
                    body=mensaje,
                    from_=self.from_number,
                    to=destino
                )
                
                logger.info(
                    f"✅ SMS enviado exitosamente. SID: {message.sid}, "
                    f"Status: {message.status}"
                )
                return True
                
            except Exception as e:
                error_str = str(e)
                
                # Si es el último intento, propagar el error
                if intento == max_intentos:
                    # Capturar errores específicos de Twilio (código original)
                    if "Unable to create record" in error_str:
                        logger.error(
                            f"❌ No se pudo enviar SMS: El número {destino} no está "
                            "verificado en tu cuenta de Twilio. Para cuentas de prueba, "
                            "debes verificar el número destino en: "
                            "https://console.twilio.com/us1/develop/phone-numbers/manage/verified"
                        )
                    elif "insufficient balance" in error_str.lower():
                        logger.error("❌ Saldo insuficiente en tu cuenta de Twilio")
                    elif "not a valid phone number" in error_str.lower():
                        logger.error(f"❌ Número de teléfono inválido: {destino}")
                    else:
                        logger.error(f"❌ Error al enviar SMS: {error_str}")
                    
                    logger.exception(e)  # Log completo del stack trace
                    return False
                
                # Si no es el último intento, hacer reintento con backoff
                logger.warning(
                    f"⚠️ Error temporal en intento {intento}/{max_intentos}: {error_str}"
                )
                
                # Esperar antes de reintentar (backoff exponencial)
                delay = 2 ** intento  # 2s, 4s, 8s
                logger.info(f"⏳ Esperando {delay}s antes de reintentar...")
                time.sleep(delay)
                
                # Reiniciar el cliente para el siguiente intento
                self._client = None
                continue
        
        # Si llegamos aquí, todos los intentos fallaron (no debería pasar)
        return False
    
    def probar_conexion(self) -> bool:
        """
        Prueba la conexión con Twilio sin enviar un SMS.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        if not self.enabled:
            logger.warning("⚠️ SMS deshabilitado")
            return False
        
        try:
            client = self._get_client()
            # Intenta obtener info de la cuenta para validar credenciales
            account = client.api.accounts(self.account_sid).fetch()
            logger.info(f"✓ Conexión exitosa. Cuenta: {account.friendly_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al probar conexión: {e}")
            return False
