#!/usr/bin/env python3
# test/test_gchat_integration.py
"""
Test script for Google Chat integration
Tests configuration, authentication, and message sending
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_chat.config import get_gchat_config
from google_chat.auth import ChatAuthConfig, build_credentials
from google_chat.client import GoogleChatClient


def test_config():
    """Test configuration loading"""
    print("=" * 70)
    print("TEST 1: Configuration")
    print("=" * 70)
    
    try:
        config = get_gchat_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Enabled: {config['enabled']}")
        print(f"  - Mode: {config['mode']}")
        print(f"  - Space: {config['space_name']}")
        print(f"  - Thread Strategy: {config['thread_strategy']}")
        return config
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return None


def test_authentication(config):
    """Test authentication"""
    print("\n" + "=" * 70)
    print("TEST 2: Authentication")
    print("=" * 70)
    
    try:
        auth_config = ChatAuthConfig(mode=config['mode'])
        creds, opts = build_credentials(auth_config)
        print(f"✓ Authentication successful")
        print(f"  - Credentials valid: {creds.valid if hasattr(creds, 'valid') else 'N/A'}")
        return auth_config
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None


def test_send_message(config, auth_config):
    """Test sending a message to the Space"""
    print("\n" + "=" * 70)
    print("TEST 3: Send Test Message")
    print("=" * 70)
    
    try:
        client = GoogleChatClient(auth_config)
        
        # Send test message
        test_message = (
            "🧪 **Test de Integración Google Chat**\n"
            "✅ Módulo `google_chat` funcionando correctamente\n"
            f"📋 Modo: `{config['mode']}`\n"
            f"🧵 Estrategia de threads: `{config['thread_strategy']}`"
        )
        
        result = client.send_text(
            space_name=config['space_name'],
            text=test_message,
            thread_key="testing"
        )
        
        print(f"✓ Message sent successfully")
        print(f"  - Message name: {result.name}")
        print(f"  - Created time: {result.create_time}")
        print(f"\n✓ Check Google Chat Space to see the message!")
        return True
        
    except Exception as e:
        print(f"✗ Send message error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🚀 Google Chat Integration Test Suite")
    print("=" * 70)
    
    # Test 1: Configuration
    config = test_config()
    if not config or not config['enabled']:
        print("\n⚠️ Google Chat is not enabled (GCHAT_ENABLED=0)")
        print("Set GCHAT_ENABLED=1 in .env to enable testing")
        return
    
    # Test 2: Authentication
    auth_config = test_authentication(config)
    if not auth_config:
        print("\n❌ Authentication failed. Cannot continue.")
        return
    
    # Test 3: Send message
    success = test_send_message(config, auth_config)
    
    # Summary
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Check Google Chat Space to see the test message")
        print("2. Run: python test/test_gchat_notifier.py")
        print("3. Run: python main.py to test full integration")
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Verify GCHAT_SPACE_NAME is correct")
        print("2. Check that credentials.json exists")
        print("3. Ensure you authorized with the correct Google account")
        print("4. Verify Space membership includes the authorized user")


if __name__ == "__main__":
    main()
