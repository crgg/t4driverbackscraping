# google_chat/strategies/space_strategy.py
"""Space notification strategy with thread support."""

from typing import Optional
from .base_strategy import NotificationStrategy
from ..client.gchat_client import GChatClient
from ..core.logger import get_logger
from ..errors.exceptions import gchat_error_boundary

logger = get_logger(__name__)


class SpaceStrategy(NotificationStrategy):
    """
    Strategy for sending notifications to a Google Chat Space.
    
    Supports organizing messages by threads for better organization.
    
    Attributes:
        space_name: Space ID (e.g., 'spaces/AAAA...')
        thread_key: Optional thread key for organizing messages
    """
    
    def __init__(self, space_name: str, thread_key: Optional[str] = None):
        """
        Initialize Space strategy.
        
        Args:
            space_name: Space ID (format: spaces/AAAA...)
            thread_key: Optional thread key to organize messages
        """
        if not space_name.startswith('spaces/'):
            raise ValueError(f"Space name must start with 'spaces/', got: {space_name}")
        
        self.space_name = space_name
        self.thread_key = thread_key
        logger.debug(f"SpaceStrategy initialized for {space_name}")
    
    @gchat_error_boundary
    def send(self, client: GChatClient, mensaje: str) -> bool:
        """
        Send notification to Space.
        
        Args:
            client: Google Chat client
            mensaje: Message text
            
        Returns:
            True if sent successfully
        """
        try:
            # Send message to space
            result = client.send_message(
                self.space_name,
                mensaje,
                thread_key=self.thread_key
            )
            
            if result:
                thread_info = f" (thread: {self.thread_key})" if self.thread_key else ""
                logger.info(f"✅ Message sent to {self.space_name}{thread_info}")
                return True
            else:
                logger.warning(f"⚠️ Failed to send to {self.space_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to space: {e}")
            return False
    
    def get_target(self) -> str:
        """Return target identifier."""
        thread_info = f" (thread: {self.thread_key})" if self.thread_key else ""
        return f"Space {self.space_name}{thread_info}"
