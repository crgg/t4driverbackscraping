# google_chat/errors/__init__.py
"""Error handling for Google Chat integration."""

from .exceptions import (
    GChatError,
    GChatAuthError,
    GChatConfigError,
    GChatAPIError,
    GChatRateLimitError,
    GChatNotFoundError,
    GChatPermissionError,
    gchat_error_boundary,
)

__all__ = [
    'GChatError',
    'GChatAuthError',
    'GChatConfigError',
    'GChatAPIError',
    'GChatRateLimitError',
    'GChatNotFoundError',
    'GChatPermissionError',
    'gchat_error_boundary',
]
