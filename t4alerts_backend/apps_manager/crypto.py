"""
Cryptography utilities for secure credential storage.
DISABLED BY USER REQUEST - PASSWORDS STORED IN PLAIN TEXT
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class CryptoService:
    """
    Dummy Service for PASS-THROUGH credentials (No Encryption).
    """
    
    def __init__(self):
        """Initialize dummy service."""
        logger.info("CryptoService initialized in PLAIN TEXT mode (Encryption Disabled)")
    
    def encrypt_credentials(self, username: str, password: str) -> Tuple[str, str]:
        """Return credentials as is."""
        return username, password
    
    def decrypt_credentials(self, encrypted_username: str, encrypted_password: str) -> Tuple[str, str]:
        """Return credentials as is."""
        return encrypted_username, encrypted_password
    
    def encrypt_string(self, plaintext: str) -> str:
        """Return string as is."""
        return plaintext
    
    def decrypt_string(self, encrypted: str) -> str:
        """Return string as is."""
        return encrypted


# Singleton instance
_crypto_service = None

def get_crypto_service() -> CryptoService:
    """Get or create the singleton CryptoService instance."""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoService()
    return _crypto_service
