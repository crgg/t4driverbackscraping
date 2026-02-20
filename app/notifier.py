# app/notifier.py
"""
Orquestador de notificaciones — Strategy Pattern.

Itera sobre CHANNELS enviando send_report() a cada canal.
Para agregar o quitar un canal basta con modificar CHANNELS; este archivo
no necesita cambios.

Para reactivar SMS:
    from sms.channel import SMSChannel
    SMSChannel.ENABLED = True
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.notification_channel import NotificationChannel
from mailer.channel import EmailChannel
from slack_comunication.channel import SlackChannel
from google_chat.channel import GChatChannel
from sms.channel import SMSChannel

if TYPE_CHECKING:
    from app.result import ScrapingResult

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ registry --
# Orden de envío: primero el más crítico/confiable.
# SMSChannel retorna False automáticamente si ENABLED = False.
CHANNELS: list[NotificationChannel] = [
    EmailChannel(),
    GChatChannel(),
    SlackChannel(),
    SMSChannel(),
]


# ---------------------------------------------------------------- public API --

def notificar_app(result: "ScrapingResult") -> None:
    """
    Envía el reporte diario a todos los canales registrados en CHANNELS.

    Args:
        result: ScrapingResult devuelto por procesar_aplicacion().
    """
    for channel in CHANNELS:
        try:
            sent = channel.send_report(result)
            if sent:
                print(f"✓ {channel.name()} enviado para {result.app_name}")
        except Exception as e:
            print(f"⚠️ {channel.name()} falló para {result.app_name}: {e}")
            logger.exception("Channel %s failed for %s", channel.name(), result.app_name)


def _send_alert_all(message: str) -> None:
    """Envía una alerta puntual a todos los canales activos."""
    for channel in CHANNELS:
        try:
            channel.send_alert(message)
        except Exception as e:
            logger.warning("Alert via %s failed: %s", channel.name(), e)


# ----------------------------------------------------- alert notifications ---

def notificar_fecha_futura(app_key: str, app_name: str, fecha_str: str) -> None:
    """
    Notifica que se intentó consultar una fecha futura.
    """
    from mailer.client import send_email, default_recipients

    mensaje_texto = (
        f"The content for date {fecha_str} has not been created yet, "
        "please check back later."
    )

    # Email (HTML enriquecido)
    subject = f"⚠️ [{app_name}] Future date query {fecha_str}"
    html_body = f"""
    <h3>Future Date Notice</h3>
    <p>Log query attempted for future date <strong>{fecha_str}</strong> in application <strong>{app_name}</strong>.</p>
    <p style="color: blue;">{mensaje_texto}</p>
    """
    sender_name = _get_alert_sender(app_key)
    try:
        recipients = default_recipients()
        send_email(subject, html_body, recipients, sender_name=sender_name)
        print(f"✓ Correo de aviso enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando correo de aviso: {e}")

    # Resto de canales con texto plano
    alert_msg = (
        f"⚠️ *{app_name}* - Future date query `{fecha_str}`\n"
        f"ℹ️ {mensaje_texto}"
    )
    for channel in CHANNELS:
        if isinstance(channel, EmailChannel):
            continue  # ya enviado arriba con HTML
        try:
            channel.send_alert(alert_msg)
        except Exception as e:
            logger.warning("Alert (future date) via %s failed: %s", channel.name(), e)


def notificar_logs_desactualizados(
    app_key: str,
    app_name: str,
    fecha_str: str,
    days_old: int,
    most_recent_date: str,
) -> None:
    """
    Notifica que los archivos de log no se han actualizado en 2+ días.
    """
    from mailer.client import send_email, default_recipients

    mensaje_texto = (
        f"WARNING: Log files have not been created for two or more days. "
        f"Most recent log is from {most_recent_date} ({days_old} days old)."
    )
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
    try:
        recipients = default_recipients()
        send_email(subject, html_body, recipients, sender_name=_get_alert_sender(app_key))
        print(f"✓ Correo de alerta de logs desactualizados enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando correo de logs desactualizados: {e}")

    alert_msg = (
        f"🚨 *DANGER: Stale Log Files*\n"
        f"*Application:* {app_name}\n"
        f"*Requested:* `{fecha_str}`\n"
        f"*Most Recent Log:* `{most_recent_date}` (*{days_old} days old*)\n"
        f"⚠️ _{mensaje_texto}_"
    )
    for channel in CHANNELS:
        if isinstance(channel, EmailChannel):
            continue
        try:
            sent = channel.send_alert(alert_msg)
            if sent:
                print(f"✓ {channel.name()} de logs desactualizados enviado para {app_name}")
        except Exception as e:
            print(f"⚠️ Error enviando {channel.name()} de logs desactualizados: {e}")


def notificar_error_conexion(
    app_key: str,
    app_name: str,
    fecha_str: str,
    error_message: str,
    max_retries: int = 3,
) -> None:
    """
    Notifica errores de conexión recurrentes después de múltiples reintentos.
    """
    from mailer.client import send_email, default_recipients

    mensaje_texto = (
        f"CRITICAL: Recurring connection errors prevented log analysis. "
        f"Failed after {max_retries} retry attempts. "
        f"This may hide critical application errors that need immediate attention."
    )
    subject = f"🚨 [{app_name}] Critical Connection Error After {max_retries} Retries"
    html_body = f"""
    <div style="background-color: #fee; border-left: 4px solid #c00; padding: 15px; margin: 10px 0;">
        <h3 style="color: #c00; margin-top: 0;">🚨 CRITICAL: Recurring Connection Error</h3>
        <p><strong>Application:</strong> {app_name}</p>
        <p><strong>Requested Date:</strong> {fecha_str}</p>
        <p><strong>Retry Attempts:</strong> {max_retries}</p>
        <hr style="border: 1px solid #c00;">
        <p style="color: #c00; font-weight: bold;">{mensaje_texto}</p>
        <p style="background-color: #fff; padding: 10px; border-left: 3px solid #666; margin: 10px 0;">
            <strong>Error Details:</strong><br>
            <code style="color: #666; font-size: 0.9em;">{error_message}</code>
        </p>
        <p style="color: #666; font-size: 0.9em;">
            ⚠️ <strong>WARNING:</strong> Connection failures may hide critical application errors.
            Investigate infrastructure and application health immediately.
        </p>
    </div>
    """
    try:
        recipients = default_recipients()
        send_email(subject, html_body, recipients, sender_name=_get_alert_sender(app_key))
        print(f"✓ Correo de error de conexión enviado para {app_name}")
    except Exception as e:
        print(f"⚠️ Error enviando correo de conexión: {e}")

    error_short = f"{error_message[:200]}{'...' if len(error_message) > 200 else ''}"
    alert_msg = (
        f"🚨 *CRITICAL: Recurring Connection Error*\n"
        f"*Application:* {app_name}\n"
        f"*Date Requested:* `{fecha_str}`\n"
        f"*Retry Attempts:* {max_retries}\n"
        f"*Error:* `{error_short}`\n"
        f"⚠️ _{mensaje_texto}_"
    )
    for channel in CHANNELS:
        if isinstance(channel, EmailChannel):
            continue
        try:
            sent = channel.send_alert(alert_msg)
            if sent:
                print(f"✓ {channel.name()} de error de conexión enviado para {app_name}")
        except Exception as e:
            print(f"⚠️ Error enviando {channel.name()} de conexión: {e}")


# ------------------------------------------------------------------ helpers --

def _get_alert_sender(app_key: str) -> str:
    """Determina el nombre del remitente según la app."""
    mapping = {
        "klc": "t4app-alerts",
        "accuratecargo": "t4app-alerts",
        "klc_crossdock": "t4app-alerts",
        "broker_goto": "brokerapp-alerts",
        "t4tms_backend": "t4tms",
    }
    return mapping.get(app_key, "driverapp-alerts")
