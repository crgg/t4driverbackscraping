# app/alerts.py  (proyecto de logs)
import os
import smtplib
import logging
from email.message import EmailMessage
from uuid import uuid4
from time import time

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _smtp_client():
    """
    Cliente SMTP muy parecido al de t4ssl, pero sin nada de anti-spam ni DB.
    Usa las mismas variables de entorno:
      MAIL_HOST, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_ENCRYPTION
    """
    host = os.getenv("MAIL_HOST", "smtp.gmail.com")
    port = int(os.getenv("MAIL_PORT", "587"))
    user = os.getenv("MAIL_USERNAME")
    pwd  = os.getenv("MAIL_PASSWORD")
    enc  = (os.getenv("MAIL_ENCRYPTION") or "tls").lower()

    if enc == "ssl":
        server = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        server = smtplib.SMTP(host, port, timeout=20)
        server.ehlo()
        server.starttls()
        server.ehlo()

    if user and pwd:
        server.login(user, pwd)

    return server


def send_email(subject: str, html_body: str, to_addrs: list[str], sender_name: str | None = None):
    """
    Envío directo, sin anti-spam.
    """
    # Limpia direcciones vacías, espacios, etc.
    to_addrs = [a.strip() for a in (to_addrs or []) if a and a.strip()]
    if not to_addrs:
        logger.info("SMTP SKIP (sin destinatarios): subject=%s", subject)
        return

    msg = EmailMessage()

    from_addr = os.getenv("MAIL_FROM_ADDRESS") or os.getenv("MAIL_USERNAME")
    from_name = sender_name or os.getenv("MAIL_FROM_NAME") or "driverapp-logs"

    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject

    # trazador opcional
    token = f"{int(time())}-{uuid4().hex[:8]}"
    msg["X-DriverApp-Logs-Token"] = token
    logger.info("SMTP SEND -> to=%s token=%s", to_addrs, token)

    msg.set_content("Revisa la versión en HTML.")
    msg.add_alternative(html_body, subtype="html")

    with _smtp_client() as s:
        s.send_message(msg)


def default_recipients(owner_email: str | None = None) -> list[str]:
    """
    Igual idea que t4ssl: si pasas un correo explícito, se usa,
    si no, se cae al ENV ALERT_EMAIL_TO o MAIL_USERNAME.
    """
    if owner_email:
        return [owner_email]

    to_env = os.getenv("ALERT_EMAIL_TO")
    if to_env:
        return [to_env]

    fallback = os.getenv("MAIL_USERNAME")
    return [fallback] if fallback else []
