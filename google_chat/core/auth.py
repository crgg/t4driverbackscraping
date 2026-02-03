# google_chat/core/auth.py
"""Authentication management for Google Chat API."""

import os
from typing import Tuple
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.credentials import Credentials

from .logger import get_logger

logger = get_logger(__name__)


class GChatAuthManager:
    """
    Manages authentication for Google Chat API using Service Account.
    
    Attributes:
        credentials_path: Path to service account JSON key file
        SCOPES: OAuth scopes required for Google Chat API
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/chat.spaces',
        'https://www.googleapis.com/auth/chat.messages',
    ]
    
    def __init__(self, credentials_path: str):
        """
        Initialize authentication manager.
        
        Args:
            credentials_path: Path to service account JSON key file
            
        Raises:
            FileNotFoundError: If credentials file doesn't exist
        """
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}"
            )
        
        self.credentials_path = credentials_path
        self._credentials: Optional[Credentials] = None
        logger.debug(f"Auth manager initialized with: {credentials_path}")
    
    def get_credentials(self) -> Credentials:
        """
        Get or create credentials with lazy loading.
        
        Returns:
            Valid credentials object
            
        Raises:
            Exception: If authentication fails
        """
        if self._credentials is None:
            self._credentials = self._load_credentials()
        
        # Refresh if expired
        if not self._credentials.valid:
            if self._credentials.expired and self._credentials.refresh_token:
                logger.debug("Refreshing expired credentials")
                self._credentials.refresh(Request())
            else:
                # Reload credentials
                self._credentials = self._load_credentials()
        
        return self._credentials
    
    def _load_credentials(self) -> Credentials:
        """
        Load credentials from service account file.
        
        Returns:
            Service account credentials
            
        Raises:
            Exception: If loading fails
        """
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            
            logger.info(
                f"✓ Credentials loaded: {credentials.service_account_email}"
            )
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Failed to load credentials: {e}")
            raise
    
    def validate_credentials(self) -> bool:
        """
        Validate that credentials are working.
        
        Returns:
            True if credentials are valid
        """
        try:
            creds = self.get_credentials()
            return creds.valid
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False
    
    def get_service_account_email(self) -> str:
        """
        Get the service account email.
        
        Returns:
            Service account email address
        """
        creds = self.get_credentials()
        if hasattr(creds, 'service_account_email'):
            return creds.service_account_email
        return "unknown"
