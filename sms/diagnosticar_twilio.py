#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la configuración de Twilio.
Ejecutar: python diagnosticar_twilio.py
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_credenciales():
    """Verifica que las credenciales estén presentes"""
    print("="*70)
    print("🔍 DIAGNÓSTICO DE TWILIO")
    print("="*70)
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    to_number = os.getenv("TWILIO_TO_NUMBER")
    
    print("\n1️⃣ Variables de entorno:")
    print(f"   TWILIO_ACCOUNT_SID: {'✓' if account_sid else '✗ FALTA'}")
    if account_sid:
        print(f"      Valor: {account_sid[:6]}...{account_sid[-4:]}")
    
    print(f"   TWILIO_AUTH_TOKEN: {'✓' if auth_token else '✗ FALTA'}")
    if auth_token:
        print(f"      Valor: {auth_token[:4]}...{auth_token[-4:]}")
    
    print(f"   TWILIO_FROM_NUMBER: {from_number if from_number else '✗ FALTA'}")
    print(f"   TWILIO_TO_NUMBER: {to_number if to_number else '✗ FALTA'}")
    
    if not all([account_sid, auth_token, from_number, to_number]):
        print("\n❌ Faltan credenciales. No se puede continuar.")
        return False
    
    return account_sid, auth_token, from_number, to_number


def verificar_cuenta(account_sid, auth_token):
    """Verifica que la cuenta de Twilio sea válida"""
    print("\n2️⃣ Verificando cuenta de Twilio...")
    
    try:
        from twilio.rest import Client
        
        # Intentar crear cliente
        client = Client(account_sid, auth_token)
        
        # Intentar obtener información de la cuenta
        account = client.api.accounts(account_sid).fetch()
        
        print(f"   ✅ Cuenta encontrada!")
        print(f"      Nombre: {account.friendly_name}")
        print(f"      Status: {account.status}")
        print(f"      Tipo: {account.type}")
        
        if account.status != "active":
            print(f"\n   ⚠️ ADVERTENCIA: La cuenta NO está activa (status: {account.status})")
            return False
        
        return True
        
    except ImportError:
        print("   ❌ ERROR: Módulo 'twilio' no instalado")
        print("      Ejecuta: pip install twilio")
        return False
    
    except Exception as e:
        error_str = str(e)
        print(f"   ❌ ERROR al verificar cuenta:")
        print(f"      {error_str}")
        
        if "20003" in error_str:
            print("\n   💡 Error 20003: Credenciales inválidas")
            print("      - Verifica que TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN sean correctos")
            print("      - Ve a: https://console.twilio.com/")
        elif "20404" in error_str:
            print("\n   💡 Error 20404: Cuenta no encontrada")
            print("      - La cuenta podría estar suspendida o eliminada")
            print("      - Verifica en: https://console.twilio.com/")
        
        return False


def verificar_numeros(client, from_number, to_number):
    """Verifica los números de teléfono"""
    print("\n3️⃣ Verificando números de teléfono...")
    
    try:
        # Verificar número de origen
        print(f"   📱 Número de origen: {from_number}")
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=from_number)
        
        if incoming_numbers:
            print("      ✅ Número de origen válido")
        else:
            print("      ⚠️ Número de origen no encontrado en tu cuenta")
            print("         Verifica en: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
        
        # Verificar número de destino (solo para cuentas Trial)
        print(f"\n   📱 Número de destino: {to_number}")
        
        # Obtener tipo de cuenta
        account = client.api.accounts.list(limit=1)[0]
        if account.type == "Trial":
            print("      ℹ️ Cuenta tipo Trial detectada")
            print("      📋 Verificando números verificados...")
            
            # Listar números verificados
            verified = client.validation_requests.list()
            verified_numbers = [v.phone_number for v in verified]
            
            if to_number in verified_numbers:
                print(f"      ✅ {to_number} está verificado")
            else:
                print(f"      ❌ {to_number} NO está verificado")
                print("         Debes verificarlo en: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
                print("\n         Números verificados actuales:")
                for num in verified_numbers:
                    print(f"            - {num}")
        else:
            print("      ✅ Cuenta completa (no Trial), puede enviar a cualquier número")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error al verificar números: {e}")
        return False


def prueba_envio(client, from_number, to_number):
    """Intenta enviar un SMS de prueba"""
    print("\n4️⃣ Prueba de envío de SMS...")
    
    respuesta = input("   ¿Deseas intentar enviar un SMS de prueba? (s/n): ")
    
    if respuesta.lower() != 's':
        print("   ⏭️ Prueba de envío omitida")
        return
    
    try:
        mensaje = "🧪 Mensaje de prueba desde diagnóstico de Twilio"
        
        print(f"   📤 Enviando SMS a {to_number}...")
        message = client.messages.create(
            body=mensaje,
            from_=from_number,
            to=to_number
        )
        
        print(f"   ✅ SMS enviado exitosamente!")
        print(f"      SID: {message.sid}")
        print(f"      Status: {message.status}")
        
    except Exception as e:
        error_str = str(e)
        print(f"   ❌ ERROR al enviar SMS:")
        print(f"      {error_str}")
        
        if "not a valid phone number" in error_str.lower():
            print("\n      💡 Número de teléfono inválido")
        elif "is not a verified phone number" in error_str.lower():
            print("\n      💡 Número no verificado (cuenta Trial)")
            print("         Verifica el número en: https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
        elif "20404" in error_str:
            print("\n      💡 Error 20404: Recurso no encontrado")
            print("         - Tu cuenta podría estar suspendida o inactiva")
            print("         - Verifica el estado en: https://console.twilio.com/")


def main():
    # Paso 1: Verificar credenciales
    result = verificar_credenciales()
    if not result:
        return
    
    account_sid, auth_token, from_number, to_number = result
    
    # Paso 2: Verificar cuenta
    cuenta_valida = verificar_cuenta(account_sid, auth_token)
    if not cuenta_valida:
        print("\n" + "="*70)
        print("❌ DIAGNÓSTICO FALLÓ: Cuenta de Twilio inválida o inactiva")
        print("="*70)
        print("\n📝 PASOS A SEGUIR:")
        print("   1. Ve a https://console.twilio.com/")
        print("   2. Verifica que tu cuenta esté activa")
        print("   3. Ve a Account > General Settings")
        print("   4. Copia el Account SID y Auth Token actualizados")
        print("   5. Actualiza tu archivo .env con las nuevas credenciales")
        return
    
    # Crear cliente para siguientes verificaciones
    from twilio.rest import Client
    client = Client(account_sid, auth_token)
    
    # Paso 3: Verificar números
    verificar_numeros(client, from_number, to_number)
    
    # Paso 4: Prueba de envío (opcional)
    prueba_envio(client, from_number, to_number)
    
    print("\n" + "="*70)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*70)


if __name__ == "__main__":
    main()
