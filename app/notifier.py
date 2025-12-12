# app/notifier.py
from typing import Dict, Any

from app.email_notifier import enviar_resumen_por_correo
from sms import enviar_sms_errores_no_controlados
from slack_comunication import enviar_slack_errores_no_controlados


def notificar_app(resultado: Dict[str, Any]) -> None:
    """
    Recibe el dict devuelto por procesar_aplicacion()
    y envía notificaciones (correo, SMS y Slack).
    """
    dia = resultado["dia"]
    app_name = resultado["app_name"]
    app_key = resultado["app_key"]

    # Enviar correo electrónico
    enviar_resumen_por_correo(dia, app_name, app_key)
    print(f"✓ Correo enviado para {app_name}")
    
    # Enviar SMS (solo si hay errores NO controlados)
    sms_enviado = enviar_sms_errores_no_controlados(resultado)
    if sms_enviado:
        print(f"✓ SMS enviado para {app_name}")
    
    # Enviar notificación a Slack (solo si hay errores NO controlados)
    slack_enviado = enviar_slack_errores_no_controlados(resultado)
    if slack_enviado:
        print(f"✓ Notificación de Slack enviada para {app_name}")
