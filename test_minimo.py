#!/usr/bin/env python3
"""
Test muy simple para identificar el problema exacto
"""
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_FROM_NUMBER")
to_number = os.getenv("TWILIO_TO_NUMBER")

from twilio.rest import Client

print("Test 1: Crear cliente y enviar inmediatamente")
print("-" * 70)
try:
    client_a = Client(account_sid, auth_token)
    msg_a = client_a.messages.create(body="Test A", from_=from_number, to=to_number)
    print(f"✅ Test A exitoso: {msg_a.sid}")
except Exception as e:
    print(f"❌ Test A falló: {e}")

print("\n\nTest 2: Crear cliente, hacer algo más, luego enviar")
print("-" * 70)
try:
    client_b = Client(account_sid, auth_token)
    # Hacer alguna operación adicional (como probar_conexion)
    account = client_b.api.accounts(account_sid).fetch()
    print(f"Account: {account.friendly_name}")
    
    # Ahora intentar enviar
    msg_b = client_b.messages.create(body="Test B", from_=from_number, to=to_number)
    print(f"✅ Test B exitoso: {msg_b.sid}")
except Exception as e:
    print(f"❌ Test B falló: {e}")

print("\n\nTest 3: Crear dos clientes separados")
print("-" * 70)
try:
    client_c1 = Client(account_sid, auth_token)
    account = client_c1.api.accounts(account_sid).fetch()
    print(f"Account: {account.friendly_name}")

    # Nuevo cliente para enviar
    client_c2 = Client(account_sid, auth_token)
    msg_c = client_c2.messages.create(body="Test C", from_=from_number, to=to_number)
    print(f"✅ Test C exitoso: {msg_c.sid}")
except Exception as e:
    print(f"❌ Test C falló: {e}")
