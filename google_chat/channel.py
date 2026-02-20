# google_chat/channel.py
"""
GChatChannel — implementación del canal de Google Chat.
Implementa NotificationChannel usando las funciones existentes de google_chat/notifier.py.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.notification_channel import NotificationChannel

if TYPE_CHECKING:
    from app.result import ScrapingResult


class GChatChannel(NotificationChannel):
    """Canal de notificación vía Google Chat Webhooks."""

    def send_report(self, result: "ScrapingResult") -> bool:
        """
        Envía el reporte de errores a Google Chat.
        La función interna decide si hay suficientes errores para notificar.
        """
        from google_chat.notifier import enviar_gchat_errores_no_controlados

        return enviar_gchat_errores_no_controlados(result.to_dict())

    def send_alert(self, message: str) -> bool:
        """Envía una alerta puntual de texto a Google Chat."""
        from google_chat.notifier import enviar_aviso_gchat

        return enviar_aviso_gchat(message)

    def name(self) -> str:
        return "Google Chat"
