# sms/channel.py
"""
SMSChannel — implementación del canal de SMS (Twilio).
Actualmente deshabilitado. Para reactivar: SMSChannel.ENABLED = True.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.notification_channel import NotificationChannel

if TYPE_CHECKING:
    from app.result import ScrapingResult


class SMSChannel(NotificationChannel):
    """
    Canal de notificación vía SMS (Twilio).

    Para reactivar sin tocar notifier.py:
        SMSChannel.ENABLED = True
    """

    ENABLED: bool = False

    def send_report(self, result: "ScrapingResult") -> bool:
        if not self.ENABLED:
            return False
        from sms.sms_notifier import enviar_sms_errores_no_controlados

        return enviar_sms_errores_no_controlados(result.to_dict())

    def send_alert(self, message: str) -> bool:
        if not self.ENABLED:
            return False
        from sms.sms_notifier import enviar_aviso_sms

        return enviar_aviso_sms(message)

    def name(self) -> str:
        return "SMS"
