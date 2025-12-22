# sms/sms_notifier.py
import logging
import time
from typing import Dict, Any
from datetime import date

from .twilio_client import TwilioSMSClient

logger = logging.getLogger(__name__)


def _contar_errores_sql(errores: list) -> int:
    """
    Cuenta cuántos errores son de tipo SQL.
    
    Args:
        errores: Lista de mensajes de error
    
    Returns:
        int: Cantidad de errores SQL
    """
    count = 0
    for error in errores:
        error_lower = error.lower()
        # Keywords relacionados con SQL y base de datos
        if any(keyword in error_lower for keyword in ['sql', 'sqlstate', 'database', 'pdo']):
            count += 1
    return count


def _generar_mensaje_sms(resultado: Dict[str, Any]) -> str:
    """
    Genera un mensaje SMS conciso reportando solo errores SQL.
    
    Formato actualizado:
    🚨 [SMS App Name]: X SQL error(s)
    Check logs immediately
    
    Args:
        resultado: Dict devuelto por procesar_aplicacion()
    
    Returns:
        str: Mensaje SMS formateado
    """
    from app.config import get_sms_app_name
    
    app_key = resultado.get("app_key", "unknown")
    no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
    
    # Contar solo errores SQL
    sql_count = _contar_errores_sql(no_controlados_nuevos)
    
    # Obtener nombre específico para SMS
    sms_app_name = get_sms_app_name(app_key)
    
    # Construir mensaje conciso (solo errores SQL)
    plural = 's' if sql_count != 1 else ''
    mensaje = (
        f"🚨 {sms_app_name}: {sql_count} SQL error{plural}\n"
        "Check logs immediately"
    )
    
    # Log del mensaje generado
    logger.debug(f"Mensaje SMS generado ({len(mensaje)} chars): {mensaje}")
    
    return mensaje


# Cliente singleton compartido para evitar race conditions
_twilio_cliente_singleton = None


def _obtener_cliente_twilio() -> TwilioSMSClient:
    """
    Obtiene o crea el cliente singleton de Twilio.
    
    Esto previene el bug donde crear múltiples clientes en rápida sucesión
    causa errores 404 en la APIREST de Twilio.
    
    Returns:
        TwilioSMSClient: Instancia singleton del cliente
    """
    global _twilio_cliente_singleton
    
    if _twilio_cliente_singleton is None:
        _twilio_cliente_singleton = TwilioSMSClient()
        logger.debug("✓ Cliente singleton de Twilio creado")
    
    return _twilio_cliente_singleton


def enviar_sms_errores_no_controlados(resultado: Dict[str, Any]) -> bool:
    """
    Envía un SMS si hay errores SQL entre los errores NO controlados.
    
    CAMBIO: Ahora solo alerta sobre errores SQL, no todos los errores NC.
    
    Esta función:
    1. Verifica si hay errores SQL entre los no controlados
    2. Genera un mensaje conciso con la cantidad de errores SQL
    3. Envía el SMS usando TwilioSMSClient
    4. Registra el resultado en logs
    
    Args:
        resultado: Dict devuelto por procesar_aplicacion() con las claves:
            - app_name: nombre de la aplicación
            - app_key: clave de la aplicación
            - dia: fecha del reporte
            - no_controlados_nuevos: lista de errores no controlados nuevos
            - controlados_nuevos: lista de errores controlados nuevos (opcional)
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    app_name = resultado.get("app_name", "App")
    app_key = resultado.get("app_key", "unknown")
    no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
    
    # Contar errores SQL
    sql_count = _contar_errores_sql(no_controlados_nuevos)
    
    # Solo enviar SMS si hay errores SQL
    if sql_count == 0:
        if len(no_controlados_nuevos) > 0:
            logger.info(
                f"ℹ️ No se envía SMS para {app_name}: "
                f"No hay errores SQL entre los {len(no_controlados_nuevos)} errores NO controlados"
            )
        else:
            logger.info(
                f"ℹ️ No se envía SMS para {app_name}: "
                "No hay errores NO controlados nuevos"
            )
        return False
    
    try:
        # Usar cliente singleton (compartido entre todos los envíos)
        cliente = _obtener_cliente_twilio()
        
        # Generar mensaje
        mensaje = _generar_mensaje_sms(resultado)
        
        # Enviar SMS
        exito = cliente.enviar_sms(mensaje)
        
        if exito:
            logger.info(
                f"✅ SMS enviado para {app_name}: "
                f"{sql_count} errores SQL detectados"
            )
            # Delay para cumplir con rate limit de Twilio Trial (1 SMS/segundo)
            # Usamos 3 segundos para dar margen y evitar errores 404
            time.sleep(3)
        else:
            logger.warning(
                f"⚠️ No se pudo enviar SMS para {app_name}"
            )
        
        return exito
    
    except Exception as e:
        # Capturar cualquier error para no interrumpir el flujo principal
        logger.error(
            f"❌ Error inesperado al enviar SMS para {app_name}: {e}",
            exc_info=True
        )
        return False


def enviar_aviso_sms(mensaje: str) -> bool:
    """
    Envía un mensaje SMS genérico.
    
    Args:
        mensaje: El contenido del mensaje a enviar.
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario.
    """
    try:
        cliente = _obtener_cliente_twilio()
        exito = cliente.enviar_sms(mensaje)
        
        if exito:
            logger.info("✅ Aviso SMS enviado")
            time.sleep(1) # Pequeña pausa por cortesía/rate limit
        else:
            logger.warning("⚠️ No se pudo enviar aviso SMS")
            
        return exito
    except Exception as e:
        logger.error(f"❌ Error enviando aviso SMS: {e}", exc_info=True)
        return False
