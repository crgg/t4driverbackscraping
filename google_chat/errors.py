# google_chat/errors.py
"""
Error handling for Google Chat API operations
Adapted from googleChatTesting/app/errors/
"""

from __future__ import annotations
import functools
import re
from typing import Callable, Any


class ChatAPIError(Exception):
    """Custom exception for Google Chat API errors"""
    def __init__(
        self,
        message: str,
        http_status: int | None = None,
        reason: str | None = None,
        details: str | None = None
    ):
        super().__init__(message)
        self.http_status = http_status
        self.reason = reason
        self.details = details


class GChatErrorHandler:
    """Handler for formatting and validating Google Chat operations"""
    
    @staticmethod
    def validate_email_or_raise(email: str) -> None:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(pattern, email):
            raise ValueError(f"Invalid email format: {email}")
    
    @staticmethod
    def alert_message(error: ChatAPIError) -> str:
        """Format error message for logging"""
        parts = [f"Google Chat API Error: {error}"]
        if error.http_status:
            parts.append(f"HTTP Status: {error.http_status}")
        if error.reason:
            parts.append(f"Reason: {error.reason}")
        if error.details:
            parts.append(f"Details: {error.details}")
        return " | ".join(parts)


def gchat_error_boundary(func: Callable) -> Callable:
    """
    Decorator to catch Google API exceptions and convert to ChatAPIError
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ChatAPIError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            # Convert Google API exceptions to ChatAPIError
            error_str = str(e)
            http_status = None
            reason = None
            details = None
            
            # Try to extract status code from error message
            if hasattr(e, 'code'):
                http_status = getattr(e, 'code', None)
            
            # Try to extract reason
            if 'PERMISSION_DENIED' in error_str:
                reason = 'PERMISSION_DENIED'
                http_status = http_status or 403
            elif 'INVALID_ARGUMENT' in error_str:
                reason = 'INVALID_ARGUMENT'
                http_status = http_status or 400
            elif 'NOT_FOUND' in error_str:
                reason = 'NOT_FOUND'
                http_status = http_status or 404
            
            raise ChatAPIError(
                message=error_str,
                http_status=http_status,
                reason=reason,
                details=details
            ) from e
    
    return wrapper
