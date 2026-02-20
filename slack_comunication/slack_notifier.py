# slack_comunication/slack_notifier.py
import logging
from typing import Dict, Any, List, Optional
from datetime import date

from .slack_client import SlackClient
from app.config import get_app_urls

logger = logging.getLogger(__name__)


class SlackMessageFormatter:
    """
    Formateador de mensajes para Slack con soporte para bloques enriquecidos.
    
    Esta clase crea mensajes con formato rico usando Block Kit de Slack,
    incluyendo secciones, divisores y campos con colores según la severidad.
    """
    
    @staticmethod
    def _contar_errores_sql(errores: List[str]) -> int:
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
    
    @staticmethod
    def crear_mensaje_texto(resultado: Dict[str, Any]) -> str:
        """
        Crea un mensaje de texto simple (fallback).
        
        Args:
            resultado: Dict devuelto por procesar_aplicacion()
        
        Returns:
            str: Mensaje de texto formateado
        """
        try:
            app_name = resultado.get("app_name", "App")
            no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
            controlados_nuevos = resultado.get("controlados_nuevos", [])
            total_nc = len(no_controlados_nuevos)
            total_c = len(controlados_nuevos)
            sql_count = SlackMessageFormatter._contar_errores_sql(no_controlados_nuevos)
            otros_count = total_nc - sql_count
            
            if total_nc > 0:
                # Hay errores no controlados
                mensaje = (
                    f"🚨 *{app_name}*: {total_nc} UNCONTROLLED errors detected\n"
                    f"SQL: {sql_count} | Others: {otros_count}\n"
                )
                if total_c > 0:
                    mensaje += f"ℹ️ Also {total_c} controlled errors\n"
                mensaje += "⚠️ Check logs immediately"
            else:
                # Solo errores controlados
                mensaje = (
                    f"ℹ️ *{app_name}*: {total_c} controlled errors registered\n"
                    f"⚠️ Check logs for details"
                )
            
            return mensaje
        
        except Exception as e:
            logger.error(f"❌ Error al crear mensaje texto: {e}", exc_info=True)
            return "🚨 Critical error detected - check logs"
    
    @staticmethod
    def crear_bloques_enriquecidos(resultado: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Crea bloques enriquecidos para Slack usando Block Kit.
        
        Args:
            resultado: Dict devuelto por procesar_aplicacion()
        
        Returns:
            list: Lista de bloques en formato Block Kit
        """
        try:
            app_name = resultado.get("app_name", "App")
            app_key = resultado.get("app_key", "unknown")
            try:
                _, _, logs_url = get_app_urls(app_key)
            except:
                logs_url = "#" # Fallback
            
            dia = resultado.get("dia", date.today())
            no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
            controlados_nuevos = resultado.get("controlados_nuevos", [])
            
            total_nc = len(no_controlados_nuevos)
            total_c = len(controlados_nuevos)
            sql_count = SlackMessageFormatter._contar_errores_sql(no_controlados_nuevos)
            otros_count = total_nc - sql_count
            
            # Determine header based on error types present
            only_controlled = total_nc == 0 and total_c > 0
            header_text = "ℹ️ Controlled Errors Registered" if only_controlled else "🚨 UNCONTROLLED Errors Detected"
            
            # Construir bloques
            bloques = []
            
            # Header con emoji de alerta
            bloques.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                    "emoji": True
                }
            })
            
            # Sección principal con información de la app
            bloques.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Application:*\n{app_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Date:*\n{dia}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Uncontrolled Errors:*\n{total_nc}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Controlled Errors:*\n{total_c}"
                    }
                ]
            })
            
            # Divisor
            bloques.append({"type": "divider"})
            
            if not only_controlled:
                # Categorización de errores no controlados
                bloques.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*📊 Uncontrolled categorization:*\n"
                            f"• SQL Errors: `{sql_count}`\n"
                            f"• Other errors: `{otros_count}`"
                        )
                    }
                })
                bloques.append({"type": "divider"})
            
            # Muestras de errores no controlados (máximo 3)
            if no_controlados_nuevos:
                errores_muestra = no_controlados_nuevos[:3]
                errores_texto = "\n".join([
                    f"{i+1}. `{error[:100]}{'...' if len(error) > 100 else ''}`"
                    for i, error in enumerate(errores_muestra)
                ])
                
                bloques.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔍 Uncontrolled error sample:*\n{errores_texto}"
                    }
                })
                
                if len(no_controlados_nuevos) > 3:
                    bloques.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_+ {len(no_controlados_nuevos) - 3} errors more..._"
                            }
                        ]
                    })
                bloques.append({"type": "divider"})
            
            # Muestras de errores controlados (máximo 3)
            if controlados_nuevos:
                errores_ctrl_muestra = controlados_nuevos[:3]
                errores_ctrl_texto = "\n".join([
                    f"{i+1}. `{error[:100]}{'...' if len(error) > 100 else ''}`"
                    for i, error in enumerate(errores_ctrl_muestra)
                ])
                
                bloques.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*ℹ️ Controlled error sample:*\n{errores_ctrl_texto}"
                    }
                })
                
                if len(controlados_nuevos) > 3:
                    bloques.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_+ {len(controlados_nuevos) - 3} controlled errors more..._"
                            }
                        ]
                    })
                bloques.append({"type": "divider"})
            
            # Footer con llamada a la acción
            bloques.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *Action required:* <{logs_url}|Check logs immediately>"
                }
            })
            
            return bloques
        
        except Exception as e:
            logger.error(f"❌ Error al crear bloques enriquecidos: {e}", exc_info=True)
            # Fallback a bloque simple
            return [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🚨 Critical error detected - check logs"
                }
            }]


# Cliente singleton compartido
_slack_cliente_singleton: Optional[SlackClient] = None


def _obtener_cliente_slack() -> SlackClient:
    """
    Obtiene o crea el cliente singleton de Slack.
    
    Returns:
        SlackClient: Instancia singleton del cliente
    """
    global _slack_cliente_singleton
    
    if _slack_cliente_singleton is None:
        _slack_cliente_singleton = SlackClient()
        logger.debug("✓ Cliente singleton de Slack creado")
    
    return _slack_cliente_singleton


def enviar_slack_errores_no_controlados(resultado: Dict[str, Any]) -> bool:
    """
    Envía una notificación a Slack si hay errores NO controlados.
    
    Esta función:
    1. Verifica si hay errores no controlados
    2. Genera un mensaje con formato enriquecido
    3. Envía la notificación usando SlackClient
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
    no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
    controlados_nuevos = resultado.get("controlados_nuevos", [])
    
    # Enviar notificación si hay errores NO controlados O errores controlados
    if not no_controlados_nuevos and not controlados_nuevos:
        logger.info(
            f"ℹ️ No se envía notificación de Slack para {app_name}: "
            "No hay errores nuevos (ni controlados ni no controlados)"
        )
        return False
    
    try:
        # Usar cliente singleton
        cliente = _obtener_cliente_slack()
        
        # Si Slack está deshabilitado, retornar False
        if not cliente.enabled:
            logger.debug(
                f"ℹ️ Slack deshabilitado, no se envía notificación para {app_name}"
            )
            return False
        
        # Crear mensaje de texto (fallback)
        formatter = SlackMessageFormatter()
        mensaje_texto = formatter.crear_mensaje_texto(resultado)
        
        # Crear bloques enriquecidos
        bloques = formatter.crear_bloques_enriquecidos(resultado)
        
        # Enviar notificación
        exito = cliente.enviar_mensaje(
            texto=mensaje_texto,
            bloques=bloques
        )
        
        if exito:
            logger.info(
                f"✅ Notificación de Slack enviada para {app_name}: "
                f"{len(no_controlados_nuevos)} errores NO controlados, "
                f"{len(controlados_nuevos)} errores controlados"
            )
        else:
            logger.warning(
                f"⚠️ No se pudo enviar notificación de Slack para {app_name}"
            )
        
        return exito
    
    except Exception as e:
        # Capturar cualquier error para no interrumpir el flujo principal
        logger.error(
            f"❌ Error inesperado al enviar notificación de Slack para {app_name}: {e}",
            exc_info=True
        )
        return False


def enviar_aviso_slack(mensaje: str) -> bool:
    """
    Envía un mensaje de texto plano a Slack.
    
    Args:
        mensaje: El texto del mensaje.
        
    Returns:
        bool: True si se envió con éxito.
    """
    try:
        cliente = _obtener_cliente_slack()
        
        if not cliente.enabled:
            return False
            
        exito = cliente.enviar_mensaje(mensaje)
        
        if exito:
            logger.info("✅ Aviso Slack enviado")
        else:
            logger.warning("⚠️ No se pudo enviar aviso Slack")
            
        return exito
    except Exception as e:
        logger.error(f"❌ Error enviando aviso Slack: {e}", exc_info=True)
        return False


def test_slack_integration() -> bool:
    """
    Prueba la integración con Slack enviando un mensaje de test.
    
    Returns:
        bool: True si la prueba es exitosa
    """
    try:
        cliente = _obtener_cliente_slack()
        
        # Test de conexión
        if not cliente.test_conexion():
            logger.error("❌ Test de conexión fallido")
            return False
        
        # Mensaje de prueba
        mensaje_prueba = (
            "🔧 *Test de Integración*\n"
            "Este es un mensaje de prueba del sistema de notificaciones.\n"
            "✅ La integración con Slack está funcionando correctamente."
        )
        
        exito = cliente.enviar_mensaje(mensaje_prueba)
        
        if exito:
            logger.info("✅ Test de integración exitoso")
        else:
            logger.error("❌ Test de integración fallido")
        
        return exito
    
    except Exception as e:
        logger.error(
            f"❌ Error al probar integración con Slack: {e}",
            exc_info=True
        )
        return False
