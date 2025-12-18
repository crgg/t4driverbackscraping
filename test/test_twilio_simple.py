#!/usr/bin/env python3
"""
Script simplificado para verificar si Twilio funciona en el contexto actual.
"""
import sys
import os

# Añadir el directorio raíz al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sms.twilio_client import TwilioSMSClient

def main():
    print("="*70)
    print("🧪 PRUEBA RÁPIDA DE TWILIO EN EL PROYECTO")
    print("="*70)
    
    print(f"\n📍 Python: {sys.executable}")
    print(f"📍 Versión: {sys.version}")
    
    # Intentar importar twilio
    try:
        import twilio
        print(f"\n✅ Twilio instalado - Versión: {twilio.__version__}")
    except ImportError:
        print("\n❌ Twilio NO está instalado en este entorno")
        print("   Ejecuta: pip install twilio")
        return
    
    # Crear cliente
    print("\n🔌 Creando TwilioSMSClient...")
    try:
        cliente = TwilioSMSClient()
        print("✅ Cliente creado exitosamente")
    except Exception as e:
        print(f"❌ Error al crear cliente: {e}")
        return
    
    # Probar conexión
    print("\n🔍 Probando conexión con Twilio...")
    if cliente.probar_conexion():
        print("✅ Conexión exitosa")
    else:
        print("❌ Fallo en la conexión")
        return
    
    # Intentar enviar SMS de prueba
    print("\n📤 Intentando enviar SMS de prueba...")
    mensaje = "🧪 Prueba desde script de verificación"
    
    try:
        exito = cliente.enviar_sms(mensaje)
        
        if exito:
            print("✅ SMS enviado exitosamente")
        else:
            print("❌ No se pudo enviar el SMS")
    except Exception as e:
        print(f"❌ Error al enviar SMS: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ PRUEBA COMPLETADA")
    print("="*70)

if __name__ == "__main__":
    main()
