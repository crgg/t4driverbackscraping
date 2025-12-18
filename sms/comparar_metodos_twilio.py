#!/usr/bin/env python3
"""
Comparación directa de dos formas de enviar SMS con Twilio
"""
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_FROM_NUMBER")
to_number = os.getenv("TWILIO_TO_NUMBER")

print("="*70)
print("🔬 COMPARACIÓN DE MÉTODOS DE ENVÍO")
print("="*70)

print(f"\nCredenciales:")
print(f"  Account SID: {account_sid}")
print(f"  From: {from_number}")
print(f"  To: {to_number}")

from twilio.rest import Client

# Método 1: Cliente normal (como en diagnosticar_twilio.py)
print("\n\n📤 MÉTODO 1: Cliente normal")
print("-" * 70)
try:
    client1 = Client(account_sid, auth_token)
    
    # Verificar tipo de cliente
    print(f"Tipo de client: {type(client1)}")
    print(f"Account SID en cliente: {client1.account_sid}")
    
    # Intentar enviar
    message1 = client1.messages.create(
        body="🧪 Prueba método 1 - Cliente normal",
        from_=from_number,
        to=to_number
    )
    
    print(f"✅ ÉXITO - SID: {message1.sid}")
    print(f"   Status: {message1.status}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")


# Método 2: Cliente creado de la misma forma que TwilioSMSClient
print("\n\n📤 MÉTODO 2: Cliente creado step-by-step")
print("-" * 70)
try:
    # Simular exactamente lo que hace TwilioSMSClient
    _client = None
    
    # Lazy loading como en _get_client()
    if _client is None:
        _client = Client(account_sid, auth_token)
        print(f"Cliente inicializado: {type(_client)}")
    
    client2 = _client
    
    print(f"Tipo de client: {type(client2)}")
    print(f"Account SID en cliente: {client2.account_sid}")
    
    # Intentar enviar
    message2 = client2.messages.create(
        body="🧪 Prueba método 2 - Cliente lazy",
        from_=from_number,
        to=to_number
    )
    
    print(f"✅ ÉXITO - SID: {message2.sid}")
    print(f"   Status: {message2.status}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")


# Método 3: Verificar si  hay algún problema con el account en contexto
print("\n\n📤 MÉTODO 3: Verificar Account Context")
print("-" * 70)
try:
    client3 = Client(account_sid, auth_token)
    
    # Verificar la cuenta
    account_info = client3.api.accounts(account_sid).fetch()
    print(f"Cuenta: {account_info.friendly_name}")
    print(f"Status: {account_info.status}")
    print(f"Tipo: {account_info.type}")
    
    # Verificar el número de origen
    print("\nNúmeros de origen disponibles:")
    numbers = client3.incoming_phone_numbers.list(limit=5)
    for num in numbers:
        print(f"  - {num.phone_number} (SID: {num.sid})")
    
    # Intentar enviar especificando explícitamente
    message3 = client3.messages.create(
        body="🧪 Prueba método 3 - Con verificación",
        from_=from_number,
        to=to_number
    )
    
    print(f"\n✅ ÉXITO - SID: {message3.sid}")
    print(f"   Status: {message3.status}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ COMPARACIÓN COMPLETADA")
print("="*70)
