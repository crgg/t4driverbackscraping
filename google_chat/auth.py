# google_chat/auth.py
"""
Authentication configuration for Google Chat API
Supports both OAuth user mode and Service Account mode
Adapted from googleChatTesting/app/core/auth.py
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Tuple, Dict, Any

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2.service_account import Credentials as SACredentials

SCOPES_USER = [
    "https://www.googleapis.com/auth/chat.spaces",
    "https://www.googleapis.com/auth/chat.spaces.create",
    "https://www.googleapis.com/auth/chat.messages.create",
    "https://www.googleapis.com/auth/chat.messages.readonly",
]

SCOPES_APP = ["https://www.googleapis.com/auth/chat.bot"]


@dataclass
class ChatAuthConfig:
    """Configuration for Google Chat authentication"""
    mode: str  # "user" | "app"


def build_credentials(cfg: ChatAuthConfig) -> Tuple[Any, Dict[str, Any]]:
    """
    Build credentials based on authentication mode
    
    Args:
        cfg: ChatAuthConfig with mode="user" or mode="app"
    
    Returns:
        Tuple of (credentials, client_options)
    """
    if cfg.mode == "user":
        creds = None
        token_file = "token.json"
        credentials_file = "credentials.json"
        
        # Load existing token if available
        if os.path.exists(token_file):
            creds = UserCredentials.from_authorized_user_file(token_file, SCOPES_USER)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise RuntimeError(
                        f"Missing {credentials_file} for OAuth user authentication. "
                        "Please download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES_USER
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_file, "w") as f:
                f.write(creds.to_json())
        
        return creds, {"scopes": SCOPES_USER}

    if cfg.mode == "app":
        sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not sa_path:
            raise RuntimeError(
                "Missing GOOGLE_APPLICATION_CREDENTIALS environment variable "
                "for Service Account authentication"
            )
        if not os.path.exists(sa_path):
            raise RuntimeError(
                f"Service account file not found: {sa_path}"
            )
        creds = SACredentials.from_service_account_file(sa_path, scopes=SCOPES_APP)
        return creds, {"scopes": SCOPES_APP}

    raise ValueError(f"Invalid auth mode: {cfg.mode}. Must be 'user' or 'app'")
