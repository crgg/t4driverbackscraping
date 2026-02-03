# google_chat/client.py
"""
Google Chat API client
Simplified version adapted from googleChatTesting/app/gchat/client.py
"""

from __future__ import annotations
from typing import Optional
from google.apps import chat_v1
from google.apps.chat_v1 import types as chat_types

from google_chat.auth import ChatAuthConfig, build_credentials
from google_chat.errors import gchat_error_boundary


class GoogleChatClient:
    """Client for interacting with Google Chat API"""
    
    def __init__(self, cfg: ChatAuthConfig):
        """
        Initialize Google Chat client
        
        Args:
            cfg: ChatAuthConfig with authentication mode
        """
        creds, client_options = build_credentials(cfg)
        self.client = chat_v1.ChatServiceClient(
            credentials=creds, 
            client_options=client_options
        )
        self.mode = cfg.mode

    @gchat_error_boundary
    def send_text(
        self,
        space_name: str,
        text: str,
        thread_key: str | None = None,
    ) -> chat_types.Message:
        """
        Send a text message to a Google Chat Space
        
        Args:
            space_name: Space resource name (e.g., "spaces/AAAAxxxxxxx")
            text: Message text (supports markdown)
            thread_key: Optional thread key for organizing messages
        
        Returns:
            Created message object
        """
        msg = chat_types.Message(text=text)

        if thread_key:
            # Send to a specific thread
            msg.thread = chat_types.Thread(thread_key=thread_key)
            req = chat_types.CreateMessageRequest(
                parent=space_name,
                message=msg,
                message_reply_option=chat_types.CreateMessageRequest.MessageReplyOption
                    .REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD
            )
        else:
            # Send as a regular message (no thread)
            req = chat_types.CreateMessageRequest(
                parent=space_name, 
                message=msg
            )

        return self.client.create_message(req)

    @gchat_error_boundary
    def list_spaces(self, filter_expr: str = 'space_type != ""'):
        """
        List available spaces
        
        Args:
            filter_expr: Filter expression for spaces
        
        Returns:
            List of Space objects
        """
        req = chat_types.ListSpacesRequest(filter=filter_expr)
        return list(self.client.list_spaces(req))

    @gchat_error_boundary
    def set_up_space(
        self, 
        display_name: str, 
        user_refs: list[str], 
        caller_user_ref: str | None = None
    ):
        """
        Create a new Space with members
        
        Args:
            display_name: Display name for the space
            user_refs: List of user references (e.g., ["users/email@domain.com"])
            caller_user_ref: Optional caller reference to exclude from members
        
        Returns:
            Created Space object
        """
        # Don't include the caller - API adds them automatically
        cleaned_refs = [r for r in user_refs if r and r != caller_user_ref]

        memberships = [
            chat_types.Membership(
                member=chat_types.User(
                    name=ref, 
                    type_=chat_types.User.Type.HUMAN
                )
            )
            for ref in cleaned_refs
        ]

        req = chat_types.SetUpSpaceRequest(
            space=chat_types.Space(
                space_type=chat_types.Space.SpaceType.SPACE,
                display_name=display_name,
            ),
            memberships=memberships,
        )
        return self.client.set_up_space(req)
