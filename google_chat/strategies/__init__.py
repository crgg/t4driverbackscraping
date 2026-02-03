# google_chat/strategies/__init__.py
"""Notification strategies for different Google Chat targets."""

from .base_strategy import NotificationStrategy
from .dm_strategy import DMStrategy
from .space_strategy import SpaceStrategy

__all__ = [
    'NotificationStrategy',
    'DMStrategy',
    'SpaceStrategy',
]
