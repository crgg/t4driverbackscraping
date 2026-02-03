# google_chat/__init__.py
"""
Google Chat integration module for T4Alerts
Sends notifications to Google Chat Spaces with threading support
"""

from google_chat.notifier import (
    enviar_gchat_errores_no_controlados,
    enviar_aviso_gchat
)

__all__ = [
    'enviar_gchat_errores_no_controlados',
    'enviar_aviso_gchat'
]
