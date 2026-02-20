# slack_comunication/channel.py
"""
SlackChannel — implementación del canal de Slack.
Implementa NotificationChannel usando las funciones existentes de slack_notifier.py.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.notification_channel import NotificationChannel

if TYPE_CHECKING:
    from app.result import ScrapingResult


class SlackChannel(NotificationChannel):
    """Canal de notificación vía Slack Webhooks."""

    def send_report(self, result: "ScrapingResult") -> bool:
        """
        Envía el reporte de errores a Slack.
        La función interna decide si hay suficientes errores para notificar.
        """
        from slack_comunication.slack_notifier import enviar_slack_errores_no_controlados

        return enviar_slack_errores_no_controlados(result.to_dict())

    def send_alert(self, message: str) -> bool:
        """Envía una alerta puntual de texto a Slack."""
        from slack_comunication.slack_notifier import enviar_aviso_slack

        return enviar_aviso_slack(message)

    def name(self) -> str:
        return "Slack"
