# google_chat/strategies/dm_strategy.py
"""Direct Message notification strategy."""

from typing import Optional
from .base_strategy import NotificationStrategy
from ..client.gchat_client import GChatClient
from ..core.logger import get_logger
from ..errors.exceptions import gchat_error_boundary

logger = get_logger(__name__)


class DMStrategy(NotificationStrategy):
    """
    Strategy for sending notifications via Direct Message.
    
    Attributes:
        user_email: Target user's email address
    """
    
    def __init__(self, user_email: str):
        """
        Initialize DM strategy.
        
        Args:
            user_email: Email address of target user
        """
        self.user_email = user_email
        self._space_name: Optional[str] = None
        logger.debug(f"DMStrategy initialized for {user_email}")
    
    @gchat_error_boundary
    def send(self, client: GChatClient, mensaje: str) -> bool:
        """
        Send notification as Direct Message.
        
        Args:
            client: Google Chat client
            mensaje: Message text
            
        Returns:
            True if sent successfully
        """
        try:
            # Get or create DM space
            if self._space_name is None:
                self._space_name = client.find_or_create_dm(self.user_email)
                if not self._space_name:
                    logger.error(f"Failed to create DM with {self.user_email}")
                    return False
            
            # Send message
            result = client.send_message(self._space_name, mensaje)
            
            if result:
                logger.info(f"✅ DM sent to {self.user_email}")
                return True
            else:
                logger.warning(f"⚠️ Failed to send DM to {self.user_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending DM: {e}")
            return False
    
    def get_target(self) -> str:
        """Return target identifier."""
        return f"DM to {self.user_email}"
