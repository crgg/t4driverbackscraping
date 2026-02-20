# mailer/channel.py
"""
EmailChannel — implementación del canal de correo electrónico.
Implementa NotificationChannel usando mailer/builder.py y mailer/client.py.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.notification_channel import NotificationChannel

if TYPE_CHECKING:
    from app.result import ScrapingResult


class EmailChannel(NotificationChannel):
    """Canal de notificación por correo electrónico (SMTP)."""

    def send_report(self, result: "ScrapingResult") -> bool:
        """
        Envía el resumen HTML de errores del día.
        No envía si no hay ningún error (controlado ni no-controlado).
        """
        from mailer.builder import enviar_resumen_por_correo

        total = result.total_controlados + result.total_no_controlados
        if total == 0:
            return False

        enviar_resumen_por_correo(result.dia, result.app_name, result.app_key)
        return True

    def send_alert(self, message: str) -> bool:
        """
        Envía una alerta puntual por correo.
        El mensaje se incluye en un HTML mínimo.
        """
        from mailer.client import send_email, default_recipients

        # Convertir saltos de línea a HTML
        html_body = f"<p>{message.replace(chr(10), '<br>')}</p>"
        subject = (message.split("\n")[0])[:120]  # primera línea como asunto

        recipients = default_recipients()
        if not recipients:
            return False

        send_email(subject, html_body, recipients)
        return True

    def name(self) -> str:
        return "Email"
