#!/usr/bin/env python3
"""
Test sending DM using OAuth2 (credentials.json).

This script uses OAuth2 authentication (acting as a user, not a bot).
It will open a browser window to authorize the first time.

Requirements:
- credentials.json in project root
- Target user email

Usage:
    python google_chat/test_oauth_dm.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.apps import chat_v1
import pickle


# OAuth scopes required
SCOPES = [
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.spaces',
]

# Paths
CREDENTIALS_FILE = project_root / 'credentials.json'
TOKEN_FILE = project_root / 'token.pickle'


def get_credentials():
    """
    Get OAuth2 credentials, prompting user to authorize if needed.
    
    Returns:
        Credentials object
    """
    creds = None
    
    # Load existing token if available
    if TOKEN_FILE.exists():
        print("📂 Loading saved token...")
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"❌ Error: credentials.json not found at: {CREDENTIALS_FILE}")
                print("\n📝 To get credentials.json:")
                print("   1. Go to: https://console.cloud.google.com/apis/credentials")
                print("   2. Create OAuth 2.0 Client ID (Desktop app)")
                print("   3. Download JSON and save as credentials.json")
                sys.exit(1)
            
            print("🔐 Starting OAuth2 flow...")
            print("   A browser window will open for authorization")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for future use
        print("💾 Saving token for future use...")
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    print("✅ Authentication successful!")
    return creds


def find_or_create_dm(service, user_email):
    """
    Find existing DM or create new one.
    
    Args:
        service: Chat service client
        user_email: Target user email
        
    Returns:
        Space name
    """
    print(f"\n📍 Finding/creating DM with {user_email}...")
    
    # Format user as resource
    if not user_email.startswith('users/'):
        user_resource = f'users/{user_email}'
    else:
        user_resource = user_email
    
    try:
        # Set up space request for DM
        request = chat_v1.SetUpSpaceRequest(
            space=chat_v1.Space(
                space_type=chat_v1.Space.SpaceType.DIRECT_MESSAGE
            )
        )
        
        space = service.set_up_space(request=request)
        print(f"✅ DM space ready: {space.name}")
        return space.name
        
    except Exception as e:
        print(f"❌ Error creating DM: {e}")
        print(f"\n💡 Alternative: Using user email directly")
        # Fallback: construct space name
        return f"spaces/DIRECT_{user_email.replace('@', '_at_')}"


def send_test_message(service, space_name, target_email):
    """
    Send a test message.
    
    Args:
        service: Chat service client
        space_name: Space to send to
        target_email: Target user email (for display)
    """
    print(f"\n📤 Sending test message to {target_email}...")
    
    message_text = (
        "🧪 **Mensaje de Prueba de T4Alerts**\n\n"
        "Este es un mensaje de prueba del sistema de notificaciones.\n\n"
        "✅ Si recibes esto, ¡la configuración funciona correctamente!\n\n"
        "---\n"
        "*Enviado desde sistema de alertas T4App*"
    )
    
    try:
        message = chat_v1.Message(text=message_text)
        
        request = chat_v1.CreateMessageRequest(
            parent=space_name,
            message=message
        )
        
        response = service.create_message(request=request)
        
        print("✅ ¡Mensaje enviado exitosamente!")
        print(f"   Message ID: {response.name}")
        print(f"\n📱 Revisa Google Chat:")
        print(f"   - Web: https://chat.google.com/")
        print(f"   - Móvil: App de Google Chat")
        print(f"   - Busca el mensaje de prueba")
        
        return True
        
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        print(f"\n📝 Posibles causas:")
        print(f"   1. Email {target_email} no tiene cuenta de Google")
        print(f"   2. Necesitas permisos adicionales")
        print(f"   3. El espacio no existe")
        return False


def main():
    """Main test flow."""
    print("=" * 70)
    print("Google Chat OAuth2 DM Test")
    print("=" * 70)
    
    # Target email (hardcoded for now, can be changed)
    TARGET_EMAIL = "ramon@t4app.com"
    
    print(f"\n👤 Target: {TARGET_EMAIL}")
    print("🔐 Auth method: OAuth2 (as user)")
    
    # Get credentials
    try:
        creds = get_credentials()
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return 1
    
    # Initialize Chat service
    print("\n🚀 Initializing Google Chat service...")
    try:
        service = chat_v1.ChatServiceClient(credentials=creds)
        print("✅ Service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return 1
    
    # Find or create DM
    try:
        space_name = find_or_create_dm(service, TARGET_EMAIL)
    except Exception as e:
        print(f"❌ Failed to get DM space: {e}")
        return 1
    
    # Send test message
    success = send_test_message(service, space_name, TARGET_EMAIL)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Test completed successfully!")
        print("=" * 70)
        print("\n💡 Next steps:")
        print("   1. Verifica que ramon@t4app.com recibió el mensaje")
        print("   2. Para producción, considera usar Service Account")
        print("   3. Ver implementation_plan.md para setup completo")
        return 0
    else:
        print("\n" + "=" * 70)
        print("❌ Test failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
