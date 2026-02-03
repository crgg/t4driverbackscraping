#!/usr/bin/env python3
"""
Test sending a message via Google Chat.

This script sends a test message to verify the full notification flow.

Run: python test_gchat_send.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_chat import enviar_aviso_gchat
from google_chat.core.logger import setup_logger

logger = setup_logger('test_send')


def main():
    """Send a test message."""
    logger.info("=" * 70)
    logger.info("Google Chat Send Test")
    logger.info("=" * 70)
    
    test_message = "🧪 **Test Message from T4Alerts**\n\nThis is a test to verify Google Chat integration is working correctly."
    
    logger.info("\n📤 Sending test message...")
    logger.info(f"Message: {test_message[:50]}...")
    
    success = enviar_aviso_gchat(test_message)
    
    if success:
        logger.info("\n✅ Message sent successfully!")
        logger.info("\n📱 Check your Google Chat:")
        logger.info("   - Open Google Chat (chat.google.com or mobile app)")
        logger.info("   - Look for DM from the Service Account bot")
        logger.info("   - Verify the test message appears")
    else:
        logger.error("\n❌ Failed to send message")
        logger.info("\n📝 Troubleshooting:")
        logger.info("   1. Run: python test_gchat_setup.py first")
        logger.info("   2. Check logs above for specific error")
        logger.info("   3. Verify GCHAT_TARGET_EMAIL in .env is correct")
        logger.info("   4. For DM mode, user email must exist")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
