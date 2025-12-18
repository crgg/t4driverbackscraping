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


def notificar_fecha_futura(app_key: str, app_name: str, fecha_str: str) -> None:
    """
    Envía notificaciones indicando que se intentó consultar una fecha futura.
    """
    from app.alerts import send_email, default_recipients
    from sms import enviar_aviso_sms
    from slack_comunication import enviar_aviso_slack
    
    mensaje_texto = (
        f"The content for date {fecha_str} has not been created yet, "
        "please check back later."
    )
    
    # 1. Email
    subject = f"⚠️ [{app_name}] Future date query {fecha_str}"
    
    # HTML simple
    html_body = f"""
    <h3>Future Date Notice</h3>
    <p>Log query attempted for future date <strong>{fecha_str}</strong> in application <strong>{app_name}</strong>.</p>
    <p style="color: blue;">{mensaje_texto}</p>
    """
    
    # Determine sender name based on app_key
    sender_name = "driverapp-alerts"  # Default
    if app_key in ["klc", "accuratecargo"]:
        sender_name = "t4app-alerts"
    elif app_key == "broker_goto":
        sender_name = "brokerapp-alerts"
    elif app_key == "t4tms_backend":
        sender_name = "t4tms"
    # For driverapp_goto and goexperior, it stays as driverapp-alerts
    
    try:
        recipients = default_recipients()
        send_email(subject, html_body, recipients, sender_name=sender_name)
        print(f"✓ Correo de aviso enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando correo de aviso: {e}")

    # 2. SMS - Mensaje corto
    # "App: [Name] - Future date [Date]. Content being created, check later."
    sms_msg = (
        f"App: {app_name[:15]} - Future date {fecha_str}. "
        "Content being created, check later."
    )
    enviar_aviso_sms(sms_msg)
    
    # 3. Slack
    slack_msg = (
        f"⚠️ *{app_name}* - Future date query `{fecha_str}`\n"
        f"ℹ️ {mensaje_texto}"
    )
    enviar_aviso_slack(slack_msg)
