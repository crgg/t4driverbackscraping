# sms/__init__.py
"""
Módulo de notificaciones SMS usando Twilio.
"""

from .sms_notifier import enviar_sms_errores_no_controlados

__all__ = ["enviar_sms_errores_no_controlados"]
