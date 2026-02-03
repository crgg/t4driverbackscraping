# app/notifier.py
from typing import Dict, Any

from app.email_notifier import enviar_resumen_por_correo
# from sms import enviar_sms_errores_no_controlados  # DESHABILITADO
from slack_comunication import enviar_slack_errores_no_controlados
from google_chat import enviar_gchat_errores_no_controlados, enviar_aviso_gchat


def notificar_app(resultado: Dict[str, Any]) -> None:
    """
    Recibe el dict devuelto por procesar_aplicacion()
    y envía notificaciones (correo, Google Chat, SMS y Slack).
    """
    dia = resultado["dia"]
    app_name = resultado["app_name"]
    app_key = resultado["app_key"]

    # Enviar correo electrónico
    enviar_resumen_por_correo(dia, app_name, app_key)
    print(f"✓ Correo enviado para {app_name}")
    
    # Enviar Google Chat (solo si hay errores NO controlados)
    try:
        gchat_enviado = enviar_gchat_errores_no_controlados(resultado)
        if gchat_enviado:
            print(f"✓ Google Chat enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando Google Chat para {app_name}: {e}")
    
    # Enviar SMS (solo si hay errores NO controlados) - DESHABILITADO
    # sms_enviado = enviar_sms_errores_no_controlados(resultado)
    # if sms_enviado:
    #     print(f"✓ SMS enviado para {app_name}")
    
    # Enviar notificación a Slack (solo si hay errores NO controlados)
    slack_enviado = enviar_slack_errores_no_controlados(resultado)
    if slack_enviado:
        print(f"✓ Notificación de Slack enviada para {app_name}")



def notificar_fecha_futura(app_key: str, app_name: str, fecha_str: str) -> None:
    """
    Envía notificaciones indicando que se intentó consultar una fecha futura.
    """
    from app.alerts import send_email, default_recipients
    # from sms import enviar_aviso_sms  # DESHABILITADO
    from slack_comunication import enviar_aviso_slack
    from google_chat import enviar_aviso_gchat
    
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
    # sms_msg = (
    #     f"App: {app_name[:15]} - Future date {fecha_str}. "
    #     "Content being created, check later."
    # )
    # enviar_aviso_sms(sms_msg)
    
    # 3. Google Chat
    gchat_msg = (
        f"⚠️ **{app_name}** - Future date query `{fecha_str}`\n"
        f"ℹ️ {mensaje_texto}"
    )
    enviar_aviso_gchat(gchat_msg)
    
    # 4. Slack
    slack_msg = (
        f"⚠️ *{app_name}* - Future date query `{fecha_str}`\n"
        f"ℹ️ {mensaje_texto}"
    )
    enviar_aviso_slack(slack_msg)


def notificar_logs_desactualizados(app_key: str, app_name: str, fecha_str: str, days_old: int, most_recent_date: str) -> None:
    """
    Envía notificaciones de peligro indicando que los archivos de log no se han actualizado en 2+ días.
    
    Args:
        app_key: Clave de la aplicación
        app_name: Nombre de la aplicación
        fecha_str: Fecha solicitada (YYYY-MM-DD)
        days_old: Número de días desde el último log
        most_recent_date: Fecha del log más reciente encontrado
    """
    from app.alerts import send_email, default_recipients
    from sms import enviar_aviso_sms
    from slack_comunication import enviar_aviso_slack
    from google_chat import enviar_aviso_gchat
    
    # Mensaje principal en inglés según requerimiento
    mensaje_texto = (
        f"WARNING: Log files have not been created for two or more days. "
        f"Most recent log is from {most_recent_date} ({days_old} days old)."
    )
    
    # 1. Email con formato de peligro
    subject = f"🚨 [{app_name}] WARNING: Stale Log Files ({days_old} days old)"
    
    html_body = f"""
    <div style="background-color: #fee; border-left: 4px solid #c00; padding: 15px; margin: 10px 0;">
        <h3 style="color: #c00; margin-top: 0;">⚠️ DANGER: Stale Log Files Detected</h3>
        <p><strong>Application:</strong> {app_name}</p>
        <p><strong>Requested Date:</strong> {fecha_str}</p>
        <p><strong>Most Recent Log:</strong> {most_recent_date}</p>
        <p><strong>Days Without Updates:</strong> {days_old} days</p>
        <hr style="border: 1px solid #c00;">
        <p style="color: #c00; font-weight: bold;">{mensaje_texto}</p>
        <p style="color: #666; font-size: 0.9em;">
            This may indicate a critical issue with the application's logging system. 
            Please investigate immediately.
        </p>
    </div>
    """
    
    # Determine sender name based on app_key
    sender_name = "driverapp-alerts"  # Default
    if app_key in ["klc", "accuratecargo", "klc_crossdock"]:
        sender_name = "t4app-alerts"
    elif app_key == "broker_goto":
        sender_name = "brokerapp-alerts"
    elif app_key == "t4tms_backend":
        sender_name = "t4tms"
    
    try:
        recipients = default_recipients()
        send_email(subject, html_body, recipients, sender_name=sender_name)
        print(f"✓ Correo de alerta de logs desactualizados enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando correo de logs desactualizados: {e}")
    
    # 2. SMS - Mensaje corto y conciso
    # sms_msg = (
    #     f"🚨 {app_name[:20]} - STALE LOGS! "
    #     f"Last update: {most_recent_date} ({days_old}d ago). Check urgently!"
    # )
    # try:
    #     enviar_aviso_sms(sms_msg)
    #     print(f"✓ SMS de alerta de logs desactualizados enviado para {app_name}")
    # except Exception as e:
    #     print(f"⚠️ Error enviando SMS de logs desactualizados: {e}")
    
    # 3. Google Chat - Formato con emojis y markdown
    gchat_msg = (
        f"🚨 **DANGER: Stale Log Files**\n"
        f"**Application:** {app_name}\n"
        f"**Requested:** `{fecha_str}`\n"
        f"**Most Recent Log:** `{most_recent_date}` (*{days_old} days old*)\n"
        f"⚠️ _{mensaje_texto}_"
    )
    try:
        enviar_aviso_gchat(gchat_msg)
        print(f"✓ Google Chat de alerta de logs desactualizados enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando Google Chat de logs desactualizados: {e}")
    
    # 4. Slack - Formato con emojis y markdown
    slack_msg = (
        f"🚨 *DANGER: Stale Log Files*\n"
        f"*Application:* {app_name}\n"
        f"*Requested:* `{fecha_str}`\n"
        f"*Most Recent Log:* `{most_recent_date}` (*{days_old} days old*)\n"
        f"⚠️ _{mensaje_texto}_"
    )
    try:
        enviar_aviso_slack(slack_msg)
        print(f"✓ Slack de alerta de logs desactualizados enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando Slack de logs desactualizados: {e}")
