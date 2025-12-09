# sms/sms_notifier.py
import logging
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
        if any(keyword in error_lower for keyword in ['sql', 'sqlstate', 'database']):
            count += 1
    return count


def _generar_mensaje_sms(resultado: Dict[str, Any]) -> str:
    """
    Genera un mensaje SMS conciso a partir del resultado del scraping.
    
    Formato del mensaje (máx 160 chars):
    🚨 [AppName]: X errores NO controlados
    SQL: Y | Otros: Z
    Revisar logs urgente
    
    Args:
        resultado: Dict devuelto por procesar_aplicacion()
    
    Returns:
        str: Mensaje SMS formateado
    """
    app_name = resultado["app_name"]
    no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
    
    total_nc = len(no_controlados_nuevos)
    sql_count = _contar_errores_sql(no_controlados_nuevos)
    otros_count = total_nc - sql_count
    
    # Versión corta del nombre de la app (máx 15 chars)
    app_short = app_name[:15] if len(app_name) > 15 else app_name
    
    # Construir mensaje conciso
    mensaje_partes = [
        f"🚨 {app_short}: {total_nc} errores NO controlados",
    ]
    
    if sql_count > 0 or otros_count > 0:
        mensaje_partes.append(f"SQL: {sql_count} | Otros: {otros_count}")
    
    mensaje_partes.append("Revisar logs urgente")
    
    mensaje = "\n".join(mensaje_partes)
    
    # Log del mensaje generado
    logger.debug(f"Mensaje SMS generado ({len(mensaje)} chars): {mensaje}")
    
    return mensaje


def enviar_sms_errores_no_controlados(resultado: Dict[str, Any]) -> None:
    """
    Envía un SMS si hay errores NO controlados en el resultado del scraping.
    
    Esta función:
    1. Verifica si hay errores no controlados
    2. Genera un mensaje conciso
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
        None
    """
    app_name = resultado.get("app_name", "App")
    app_key = resultado.get("app_key", "unknown")
    no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
    
    # Solo enviar SMS si hay errores NO controlados
    if not no_controlados_nuevos:
        logger.info(
            f"ℹ️ No se envía SMS para {app_name}: "
            "No hay errores NO controlados nuevos"
        )
        return
    
    try:
        # Inicializar cliente de Twilio
        cliente = TwilioSMSClient()
        
        # Generar mensaje
        mensaje = _generar_mensaje_sms(resultado)
        
        # Enviar SMS
        exito = cliente.enviar_sms(mensaje)
        
        if exito:
            logger.info(
                f"✅ SMS enviado para {app_name}: "
                f"{len(no_controlados_nuevos)} errores NO controlados"
            )
        else:
            logger.warning(
                f"⚠️ No se pudo enviar SMS para {app_name}"
            )
    
    except Exception as e:
        # Capturar cualquier error para no interrumpir el flujo principal
        logger.error(
            f"❌ Error inesperado al enviar SMS para {app_name}: {e}",
            exc_info=True
        )
