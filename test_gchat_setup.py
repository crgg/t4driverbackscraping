#!/usr/bin/env python3
"""
Test Google Chat authentication and configuration.

This script verifies that:
1. Configuration is loaded correctly from .env
2. Service Account credentials are valid
3. Client can authenticate with Google Chat API

Run: python test_gchat_setup.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_chat.core.config import GChatConfig
from google_chat.core.auth import GChatAuthManager
from google_chat.core.logger import setup_logger

logger = setup_logger('test_gchat')


def test_configuration():
    """Test configuration loading."""
    logger.info("📋 Testing configuration...")
    
    try:
        config = GChatConfig.from_env()
        logger.info(f"✅ Configuration loaded successfully")
        logger.info(f"   - Enabled: {config.enabled}")
        logger.info(f"   - Mode: {config.notification_mode}")
        logger.info(f"   - Credentials: {config.credentials_path}")
        
        if config.notification_mode == 'dm':
            logger.info(f"   - Target Email: {config.target_email}")
        elif config.notification_mode == 'space':
            logger.info(f"   - Space: {config.space_name}")
            if config.thread_key:
                logger.info(f"   - Thread Key: {config.thread_key}")
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        return None


def test_authentication(config):
    """Test Service Account authentication."""
    logger.info("\n🔐 Testing authentication...")
    
    try:
        auth_manager = GChatAuthManager(config.credentials_path)
        credentials = auth_manager.get_credentials()
        
        logger.info(f"✅ Authentication successful")
        logger.info(f"   - Service Account: {auth_manager.get_service_account_email()}")
        logger.info(f"   - Valid: {credentials.valid}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        return False


def test_client_initialization(config):
    """Test Google Chat client initialization."""
    logger.info("\n🚀 Testing client initialization...")
    
    try:
        from google_chat.client.gchat_client import GChatClient
        from google_chat.core.auth import GChatAuthManager
        
        auth_manager = GChatAuthManager(config.credentials_path)
        client = GChatClient(auth_manager)
        
        # Try to list spaces (this will fail gracefully if no access)
        spaces = client.list_spaces()
        
        logger.info(f"✅ Client initialized successfully")
        logger.info(f"   - Accessible spaces: {len(spaces) if spaces else 0}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Client initialization error: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("Google Chat Setup Test")
    logger.info("=" * 70)
    
    # Test 1: Configuration
    config = test_configuration()
    if not config:
        logger.error("\n❌ Setup failed: Configuration error")
        return 1
    
    if not config.enabled:
        logger.warning("\n⚠️ Google Chat is disabled (GCHAT_ENABLED=0)")
        logger.warning("Set GCHAT_ENABLED=1 in .env to enable")
        return 0
    
    # Test 2: Authentication
    if not test_authentication(config):
        logger.error("\n❌ Setup failed: Authentication error")
        logger.info("\n📝 Troubleshooting:")
        logger.info("   1. Check GOOGLE_APPLICATION_CREDENTIALS path in .env")
        logger.info("   2. Verify service-account-key.json exists and is valid")
        logger.info("   3. Ensure Service Account has Chat API access")
        return 1
    
    # Test 3: Client
    if not test_client_initialization(config):
        logger.error("\n❌ Setup failed: Client error")
        return 1
    
    # Success!
    logger.info("\n" + "=" * 70)
    logger.info("✅ All tests passed! Google Chat is ready to use.")
    logger.info("=" * 70)
    logger.info("\n📝 Next steps:")
    logger.info("   1. Run: python test_gchat_send.py")
    logger.info("   2. Then: python main.py (to test full integration)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
