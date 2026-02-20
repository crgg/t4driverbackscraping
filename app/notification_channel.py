# app/notification_channel.py
"""
NotificationChannel — Interfaz abstracta (Strategy Pattern) para canales de notificación.

Cada canal (email, Slack, Google Chat, SMS) implementa esta interfaz.
app/notifier.py solo interactúa con esta interfaz, nunca con las implementaciones
directamente, lo que permite agregar/quitar canales sin tocar el orquestador.

Implementaciones:
    mailer/channel.py          → EmailChannel
    slack_comunication/channel.py → SlackChannel
    google_chat/channel.py     → GChatChannel
    sms/channel.py             → SMSChannel (disabled stub)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.result import ScrapingResult


class NotificationChannel(ABC):
    """
    Interfaz que todo canal de notificación debe implementar.

    send_report() — Envía el reporte regular de errores del día.
    send_alert()  — Envía alertas puntuales (fecha futura, stale logs, conexión).
    """

    @abstractmethod
    def send_report(self, result: "ScrapingResult") -> bool:
        """
        Envía el reporte diario de errores.

        Args:
            result: ScrapingResult con todos los errores clasificados.

        Returns:
            True si la notificación fue enviada, False si se omitió
            (ej. canal deshabilitado, sin errores relevantes para el canal).
        """

    @abstractmethod
    def send_alert(self, message: str) -> bool:
        """
        Envía una alerta puntual en texto plano/markdown.
        Usada para: fecha futura, stale logs, error de conexión.

        Args:
            message: Texto de la alerta (puede contener markdown básico).

        Returns:
            True si fue enviada, False si se omitió.
        """

    def name(self) -> str:
        """Nombre legible del canal para logs."""
        return self.__class__.__name__
