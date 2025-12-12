# slack_comunication/__init__.py
"""
Módulo de comunicación con Slack para notificaciones de errores críticos.

Este módulo proporciona funcionalidades para enviar notificaciones a canales de Slack
cuando se detectan errores críticos en los logs de las aplicaciones.
"""

from .slack_notifier import enviar_slack_errores_no_controlados

__all__ = ["enviar_slack_errores_no_controlados"]
