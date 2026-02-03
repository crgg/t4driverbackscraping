# google_chat/client/gchat_client.py
"""Google Chat API client with retry logic and error handling."""

import time
from typing import Optional, List
from google.apps import chat_v1
from google.api_core import exceptions as google_exceptions
from google.api_core import retry

from ..core.auth import GChatAuthManager
from ..core.logger import get_logger
from ..errors.exceptions import (
    GChatAPIError,
    GChatRateLimitError,
    GChatNotFoundError,
    GChatPermissionError,
    gchat_error_boundary,
)

logger = get_logger(__name__)


class GChatClient:
    """
    Wrapper around Google Chat API with error handling and retry logic.
    
    Attributes:
        auth_manager: Authentication manager
        _service: Google Chat service client (lazy loaded)
    """
    
    def __init__(self, auth_manager: GChatAuthManager):
        """
        Initialize Google Chat client.
        
        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self._service: Optional[chat_v1.ChatServiceClient] = None
        logger.debug("GChatClient initialized")
    
    def _get_service(self) -> chat_v1.ChatServiceClient:
        """
        Get or create Chat service client (lazy loading).
        
        Returns:
            ChatServiceClient instance
        """
        if self._service is None:
            try:
                credentials = self.auth_manager.get_credentials()
                self._service = chat_v1.ChatServiceClient(credentials=credentials)
                logger.info("✓ Chat service client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Chat service: {e}")
                raise GChatAPIError(f"Failed to initialize service: {e}")
        
        return self._service
    
    @gchat_error_boundary
    def send_message(
        self,
        parent: str,
        text: str,
        thread_key: Optional[str] = None
    ) -> Optional[chat_v1.Message]:
        """
        Send a message to a space or DM.
        
        Args:
            parent: Space name (e.g., 'spaces/AAAA...')
            text: Message text (supports markdown)
            thread_key: Optional thread key for organizing messages
            
        Returns:
            Message object if successful, None on error
            
        Raises:
            GChatAPIError: If API request fails
        """
        try:
            service = self._get_service()
            
            # Create message object
            message = chat_v1.Message(text=text)
            
            # Add thread if specified
            if thread_key:
                message.thread = chat_v1.Thread(thread_key=thread_key)
            
            # Create request
            request = chat_v1.CreateMessageRequest(
                parent=parent,
                message=message
            )
            
            logger.debug(f"Sending message to {parent}")
            
            # Send with retry
            response = service.create_message(request=request)
            
            logger.info(f"✅ Message sent: {response.name}")
            return response
            
        except google_exceptions.NotFound as e:
            raise GChatNotFoundError(f"Space not found: {parent}", status_code=404)
        
        except google_exceptions.PermissionDenied as e:
            raise GChatPermissionError(
                f"Permission denied for {parent}. "
                "Check Service Account has access to this space.",
                status_code=403
            )
        
        except google_exceptions.ResourceExhausted as e:
            raise GChatRateLimitError(
                "Rate limit exceeded. Slow down requests.",
                status_code=429
            )
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise GChatAPIError(f"Failed to send message: {e}")
    
    @gchat_error_boundary
    def find_or_create_dm(self, user_email: str) -> Optional[str]:
        """
        Find existing DM or create new one with user.
        
        IMPORTANT: For Service Accounts to send DMs, the Chat app must be
        configured and published. Users must add the app before receiving DMs.
        
        Args:
            user_email: User's email address
            
        Returns:
            Space name (e.g., 'spaces/AAAA...') if successful
            
        Raises:
            GChatAPIError: If operation fails
        """
        try:
            service = self._get_service()
            
            logger.debug(f"Setting up DM space for {user_email}")
            
            # Create DM space using setup_space
            space = chat_v1.Space(
                space_type=chat_v1.Space.SpaceType.DIRECT_MESSAGE
            )
            
            request = chat_v1.SetUpSpaceRequest(
                space=space
            )
            
            # This creates/gets the DM space
            response = service.set_up_space(request=request)
            
            logger.info(f"✓ DM space ready: {response.name}")
            return response.name
            
        except google_exceptions.PermissionDenied as e:
            logger.error(
                f"Permission denied creating DM. "
                f"The Chat app must be configured and the user must add it first. "
                f"Error: {e}"
            )
            raise GChatPermissionError(
                "Cannot create DM. User must add the Chat app first.",
                status_code=403
            )
        
        except Exception as e:
            logger.error(f"Error creating DM: {e}")
            raise GChatAPIError(f"Failed to create DM: {e}")
    
    @gchat_error_boundary
    def create_space(
        self,
        display_name: str,
        member_emails: List[str]
    ) -> Optional[chat_v1.Space]:
        """
        Create a new space with members.
        
        Args:
            display_name: Name of the space
            member_emails: List of member email addresses
            
        Returns:
            Space object if successful
            
        Raises:
            GChatAPIError: If creation fails
        """
        try:
            service = self._get_service()
            
            logger.debug(f"Creating space: {display_name}")
            
            # Create space object
            space = chat_v1.Space(
                display_name=display_name,
                space_type=chat_v1.Space.SpaceType.SPACE
            )
            
            request = chat_v1.CreateSpaceRequest(space=space)
            
            # Create with retry
            response = service.create_space(request=request)
            
            logger.info(f"✅ Space created: {response.name}")
            
            # Add members
            for email in member_emails:
                try:
                    self.add_member(response.name, email)
                except Exception as e:
                    logger.warning(f"Failed to add member {email}: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating space: {e}")
            raise GChatAPIError(f"Failed to create space: {e}")
    
    @gchat_error_boundary
    def add_member(self, space_name: str, user_email: str) -> bool:
        """
        Add a member to a space.
        
        Args:
            space_name: Space ID
            user_email: User's email address
            
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            
            if not user_email.startswith('users/'):
                user_resource = f'users/{user_email}'
            else:
                user_resource = user_email
            
            membership = chat_v1.Membership(
                member=chat_v1.User(name=user_resource)
            )
            
            request = chat_v1.CreateMembershipRequest(
                parent=space_name,
                membership=membership
            )
            
            service.create_membership(request=request)
            logger.info(f"✓ Added {user_email} to {space_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding member: {e}")
            return False
    
    @gchat_error_boundary
    def list_spaces(self) -> List[chat_v1.Space]:
        """
        List all accessible spaces.
        
        Returns:
            List of Space objects
        """
        try:
            service = self._get_service()
            
            request = chat_v1.ListSpacesRequest()
            
            # Get first page
            page_result = service.list_spaces(request=request)
            
            spaces = list(page_result)
            logger.info(f"✓ Found {len(spaces)} accessible spaces")
            
            return spaces
            
        except Exception as e:
            logger.error(f"Error listing spaces: {e}")
            return []
