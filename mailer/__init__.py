# mailer/__init__.py
"""
Módulo de correo electrónico del proyecto T4Alerts.
Contiene el cliente SMTP y el constructor de contenido de correos.
"""
from mailer.client import send_email, default_recipients
from mailer.builder import enviar_resumen_por_correo, construir_html_resumen

__all__ = [
    "send_email",
    "default_recipients",
    "enviar_resumen_por_correo",
    "construir_html_resumen",
]
