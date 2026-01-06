"""
Cryptography utilities for secure credential storage.
Uses Fernet symmetric encryption to protect usernames and passwords.
"""
import os
import logging
from cryptography.fernet import Fernet, InvalidToken
from typing import Tuple

logger = logging.getLogger(__name__)


class CryptoService:
    """
    Service for encrypting and decrypting sensitive credentials.
    """
    
    def __init__(self):
        """Initialize the crypto service with the encryption key from environment."""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            raise RuntimeError(
                "ENCRYPTION_KEY not found in environment variables. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        try:
            self.cipher = Fernet(encryption_key.encode())
            logger.info("CryptoService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CryptoService: {e}")
            raise RuntimeError(f"Invalid ENCRYPTION_KEY: {e}")
    
    def encrypt_credentials(self, username: str, password: str) -> Tuple[str, str]:
        """
        Encrypt username and password.
        
        Args:
            username: Plaintext username
            password: Plaintext password
        
        Returns:
            Tuple of (encrypted_username, encrypted_password) as base64 strings
        
        Raises:
            RuntimeError: If encryption fails
        """
        try:
            encrypted_username = self.cipher.encrypt(username.encode()).decode()
            encrypted_password = self.cipher.encrypt(password.encode()).decode()
            
            logger.debug(f"Credentials encrypted successfully for user: {username[:3]}***")
            return encrypted_username, encrypted_password
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise RuntimeError(f"Failed to encrypt credentials: {e}")
    
    def decrypt_credentials(self, encrypted_username: str, encrypted_password: str) -> Tuple[str, str]:
        """
        Decrypt username and password.
        
        Args:
            encrypted_username: Encrypted username (base64 string)
            encrypted_password: Encrypted password (base64 string)
        
        Returns:
            Tuple of (plaintext_username, plaintext_password)
        
        Raises:
            RuntimeError: If decryption fails
        """
        try:
            username = self.cipher.decrypt(encrypted_username.encode()).decode()
            password = self.cipher.decrypt(encrypted_password.encode()).decode()
            
            logger.debug(f"Credentials decrypted successfully for user: {username[:3]}***")
            return username, password
            
        except InvalidToken:
            logger.error("Invalid token during decryption - possible key mismatch")
            raise RuntimeError("Failed to decrypt credentials: Invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise RuntimeError(f"Failed to decrypt credentials: {e}")
    
    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a single string.
        
        Args:
            plaintext: String to encrypt
        
        Returns:
            Encrypted string (base64)
        """
        try:
            return self.cipher.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"String encryption failed: {e}")
            raise RuntimeError(f"Failed to encrypt string: {e}")
    
    def decrypt_string(self, encrypted: str) -> str:
        """
        Decrypt a single string.
        
        Args:
            encrypted: Encrypted string (base64)
        
        Returns:
            Plaintext string
        """
        try:
            return self.cipher.decrypt(encrypted.encode()).decode()
        except InvalidToken:
            logger.error("Invalid token during string decryption")
            raise RuntimeError("Failed to decrypt string: Invalid encryption key")
        except Exception as e:
            logger.error(f"String decryption failed: {e}")
            raise RuntimeError(f"Failed to decrypt string: {e}")


# Singleton instance
_crypto_service = None

def get_crypto_service() -> CryptoService:
    """Get or create the singleton CryptoService instance."""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoService()
    return _crypto_service
