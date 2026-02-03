# google_chat/core/config.py
"""Configuration management for Google Chat integration."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class GChatConfig:
    """
    Configuration for Google Chat notifications.
    
    Attributes:
        enabled: Whether Google Chat notifications are enabled
        credentials_path: Path to Service Account JSON key file
        notification_mode: Notification strategy ('dm', 'group', 'space')
        target_email: Target user email for DM mode
        space_name: Target space ID for space mode
        thread_key: Optional thread key for organizing messages
    """
    enabled: bool
    credentials_path: str
    notification_mode: str
    target_email: Optional[str] = None
    space_name: Optional[str] = None
    thread_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'GChatConfig':
        """
        Load configuration from environment variables.
        
        Environment variables:
            GCHAT_ENABLED: 1 to enable, 0 to disable
            GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON
            GCHAT_MODE: 'dm', 'group', or 'space'
            GCHAT_TARGET_EMAIL: Email for DM mode
            GCHAT_SPACE_NAME: Space ID for space mode
            GCHAT_THREAD_KEY: Optional thread key
            
        Returns:
            GChatConfig instance
            
        Raises:
            ValueError: If required configuration is missing
        """
        enabled = os.getenv('GCHAT_ENABLED', '0') == '1'
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
        notification_mode = os.getenv('GCHAT_MODE', 'dm').lower()
        target_email = os.getenv('GCHAT_TARGET_EMAIL')
        space_name = os.getenv('GCHAT_SPACE_NAME')
        thread_key = os.getenv('GCHAT_THREAD_KEY')
        
        # Validate required fields
        if enabled and not credentials_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS must be set when GCHAT_ENABLED=1"
            )
        
        if enabled and notification_mode not in ['dm', 'group', 'space']:
            raise ValueError(
                f"GCHAT_MODE must be 'dm', 'group', or 'space', got: {notification_mode}"
            )
        
        # Mode-specific validation
        if enabled and notification_mode == 'dm' and not target_email:
            raise ValueError(
                "GCHAT_TARGET_EMAIL must be set when GCHAT_MODE=dm"
            )
        
        if enabled and notification_mode == 'space' and not space_name:
            raise ValueError(
                "GCHAT_SPACE_NAME must be set when GCHAT_MODE=space"
            )
        
        return cls(
            enabled=enabled,
            credentials_path=credentials_path,
            notification_mode=notification_mode,
            target_email=target_email,
            space_name=space_name,
            thread_key=thread_key
        )
    
    def validate(self) -> None:
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.enabled:
            return
        
        # Check credentials file exists
        if not os.path.exists(self.credentials_path):
            raise ValueError(
                f"Credentials file not found: {self.credentials_path}"
            )
        
        # Validate email format for DM mode
        if self.notification_mode == 'dm' and self.target_email:
            if '@' not in self.target_email:
                raise ValueError(
                    f"Invalid email format: {self.target_email}"
                )
        
        # Validate space name format
        if self.notification_mode == 'space' and self.space_name:
            if not self.space_name.startswith('spaces/'):
                raise ValueError(
                    f"Space name must start with 'spaces/', got: {self.space_name}"
                )
