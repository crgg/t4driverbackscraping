# test_slack_integration.py
"""
Script de prueba para verificar la integración con Slack.

Este script:
1. Verifica la configuración de las variables de entorno
2. Prueba la conexión con Slack
3. Envía un mensaje de prueba
4. Simula una notificación de error
"""

import os
import sys
from datetime import date
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slack_comunication import enviar_slack_errores_no_controlados
from slack_comunication.slack_client import SlackClient
from slack_comunication.slack_notifier import test_slack_integration


def verificar_configuracion():
    """Verifica que las variables de entorno estén configuradas."""
    print("=" * 70)
    print("🔍 VERIFICANDO CONFIGURACIÓN")
    print("=" * 70)
    
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    channel = os.getenv("SLACK_CHANNEL", "#errores-criticos")
    enabled = os.getenv("SLACK_ENABLED", "1")
    
    print(f"SLACK_BOT_TOKEN: {'✓ Configurado' if bot_token else '✗ No configurado'}")
    if bot_token:
        print(f"  Token: {bot_token[:20]}{'*' * 20}")
    
    print(f"SLACK_WEBHOOK_URL: {'✓ Configurado' if webhook_url else '✗ No configurado'}")
    if webhook_url:
        print(f"  URL: {webhook_url[:40]}...")
    
    print(f"SLACK_CHANNEL: {channel}")
    print(f"SLACK_ENABLED: {enabled}")
    
    if not bot_token and not webhook_url:
        print("\n⚠️ ADVERTENCIA: No se configuró ni SLACK_BOT_TOKEN ni SLACK_WEBHOOK_URL")
        print("   Las notificaciones de Slack estarán deshabilitadas.")
        return False
    
    print("\n✓ Configuración básica OK")
    return True


def probar_conexion():
    """Prueba la conexión con Slack."""
    print("\n" + "=" * 70)
    print("🔗 PROBANDO CONEXIÓN CON SLACK")
    print("=" * 70)
    
    try:
        cliente = SlackClient()
        
        if not cliente.enabled:
            print("⚠️ Slack deshabilitado")
            return False
        
        exito = cliente.test_conexion()
        
        if exito:
            print("✅ Conexión exitosa")
        else:
            print("❌ Conexión fallida")
        
        return exito
    
    except Exception as e:
        print(f"❌ Error al probar conexión: {e}")
        import traceback
        traceback.print_exc()
        return False


def enviar_mensaje_prueba():
    """Envía un mensaje de prueba usando la función de test."""
    print("\n" + "=" * 70)
    print("📤 ENVIANDO MENSAJE DE PRUEBA")
    print("=" * 70)
    
    try:
        exito = test_slack_integration()
        
        if exito:
            print("✅ Mensaje de prueba enviado correctamente")
        else:
            print("❌ No se pudo enviar el mensaje de prueba")
        
        return exito
    
    except Exception as e:
        print(f"❌ Error al enviar mensaje de prueba: {e}")
        import traceback
        traceback.print_exc()
        return False


def simular_notificacion_error():
    """Simula una notificación de error como las que envía el sistema."""
    print("\n" + "=" * 70)
    print("🚨 SIMULANDO NOTIFICACIÓN DE ERROR")
    print("=" * 70)
    
    # Crear un resultado simulado
    resultado_simulado = {
        "app_name": "Aplicación de Prueba",
        "app_key": "test_app",
        "dia": date.today(),
        "no_controlados_nuevos": [
            "ERROR: SQL Error - Connection timeout to database server",
            "ERROR: NullPointerException in UserController.java:123",
            "ERROR: Failed to load resource: /static/css/styles.css",
            "SQLSTATE[42S02]: Base table or view not found: 'users'",
            "ERROR: Unauthorized access attempt to /admin/panel",
        ],
        "controlados_nuevos": []
    }
    
    try:
        exito = enviar_slack_errores_no_controlados(resultado_simulado)
        
        if exito:
            print("✅ Notificación de error enviada correctamente")
            print(f"   - App: {resultado_simulado['app_name']}")
            print(f"   - Errores: {len(resultado_simulado['no_controlados_nuevos'])}")
        else:
            print("❌ No se pudo enviar la notificación de error")
        
        return exito
    
    except Exception as e:
        print(f"❌ Error al enviar notificación: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal que ejecuta todas las pruebas."""
    print("\n")
    print("=" * 70)
    print(" TEST DE INTEGRACIÓN CON SLACK")
    print("=" * 70)
    print()
    
    # 1. Verificar configuración
    if not verificar_configuracion():
        print("\n⚠️ Por favor configura las variables de entorno necesarias en .env")
        return
    
    # 2. Probar conexión
    if not probar_conexion():
        print("\n❌ La conexión con Slack falló. Verifica tu configuración.")
        return
    
    # 3. Enviar mensaje de prueba
    input("\nPresiona Enter para enviar un mensaje de prueba a Slack...")
    if not enviar_mensaje_prueba():
        print("\n⚠️ El mensaje de prueba falló, pero continuamos con las pruebas...")
    
    # 4. Simular notificación de error
    input("\nPresiona Enter para enviar una notificación de error simulada...")
    simular_notificacion_error()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 70)
    print("\nRevisa tu canal de Slack para ver los mensajes enviados.")
    print()


if __name__ == "__main__":
    main()
