# google_chat/__init__.py
"""
Google Chat notification module for T4Alerts.

Provides a scalable notification system using Google Chat API as an
alternative to Twilio SMS. Supports Direct Messages, Group Chats, and Spaces.

Example usage:
    from google_chat import enviar_gchat_errores_no_controlados
    
    resultado = {
        'app_name': 'DriveApp',
        'app_key': 'driverapp_goto',
        'fecha_str': '2026-02-02',
        'no_controlados_nuevos': ['SQL error...', 'Another error...']
    }
    
    success = enviar_gchat_errores_no_controlados(resultado)
"""

from .notifier.gchat_notifier import (
    enviar_gchat_errores_no_controlados,
    enviar_aviso_gchat,
)

__version__ = '1.0.0'

__all__ = [
    'enviar_gchat_errores_no_controlados',
    'enviar_aviso_gchat',
]
