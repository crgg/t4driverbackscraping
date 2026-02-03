# google_chat/errors/exceptions.py
"""Custom exceptions for Google Chat operations."""

from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger('google_chat.errors')


class GChatError(Exception):
    """Base exception for all Google Chat errors."""
    pass


class GChatAuthError(GChatError):
    """Raised when authentication fails."""
    pass


class GChatConfigError(GChatError):
    """Raised when configuration is invalid."""
    pass


class GChatAPIError(GChatError):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class GChatRateLimitError(GChatAPIError):
    """Raised when rate limit is exceeded."""
    pass


class GChatNotFoundError(GChatAPIError):
    """Raised when resource is not found."""
    pass


class GChatPermissionError(GChatAPIError):
    """Raised when permission is denied."""
    pass


def gchat_error_boundary(func: Callable) -> Callable:
    """
    Decorator to catch and log Google Chat errors gracefully.
    
    This prevents Google Chat errors from crashing the main application.
    Errors are logged but the function returns False on failure.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that returns bool on completion
        
    Usage:
        @gchat_error_boundary
        def send_notification(self, message):
            # Implementation
            return True
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> bool:
        try:
            result = func(*args, **kwargs)
            # If function returns True/False, pass it through
            # If it returns None or other value, consider it success
            return result if isinstance(result, bool) else True
            
        except GChatConfigError as e:
            logger.error(f"❌ Configuration error in {func.__name__}: {e}")
            return False
            
        except GChatAuthError as e:
            logger.error(f"❌ Authentication error in {func.__name__}: {e}")
            return False
            
        except GChatRateLimitError as e:
            logger.warning(
                f"⚠️ Rate limit exceeded in {func.__name__}: {e}. "
                "Consider reducing notification frequency."
            )
            return False
            
        except GChatNotFoundError as e:
            logger.error(f"❌ Resource not found in {func.__name__}: {e}")
            return False
            
        except GChatPermissionError as e:
            logger.error(
                f"❌ Permission denied in {func.__name__}: {e}. "
                "Check Service Account permissions."
            )
            return False
            
        except GChatAPIError as e:
            logger.error(
                f"❌ API error in {func.__name__}: {e}"
                f"{f' (Status: {e.status_code})' if e.status_code else ''}"
            )
            return False
            
        except GChatError as e:
            logger.error(f"❌ Google Chat error in {func.__name__}: {e}")
            return False
            
        except Exception as e:
            logger.exception(
                f"❌ Unexpected error in {func.__name__}: {e}"
            )
            return False
    
    return wrapper
