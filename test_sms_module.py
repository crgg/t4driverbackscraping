#!/usr/bin/env python3
# test_sms_module.py
"""
Script de prueba para el módulo SMS de Twilio.

Uso:
    python test_sms_module.py
"""

import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from sms.twilio_client import TwilioSMSClient
from sms.sms_notifier import enviar_sms_errores_no_controlados
from datetime import date


def test_cliente_basico():
    """Prueba 1: Inicializar cliente y verificar credenciales"""
    print("\n" + "="*70)
    print("PRUEBA 1: Inicialización del cliente de Twilio")
    print("="*70)
    
    try:
        cliente = TwilioSMSClient()
        print(f"✓ Cliente inicializado")
        print(f"  - Habilitado: {cliente.enabled}")
        print(f"  - Número origen: {cliente.from_number}")
        print(f"  - Número destino: {cliente.to_number}")
        return cliente
    except Exception as e:
        print(f"✗ Error al inicializar cliente: {e}")
        return None


def test_probar_conexion(cliente: TwilioSMSClient):
    """Prueba 2: Probar conexión con Twilio"""
    print("\n" + "="*70)
    print("PRUEBA 2: Probando conexión con Twilio")
    print("="*70)
    
    if not cliente:
        print("✗ Cliente no disponible, saltando prueba")
        return False
    
    try:
        exito = cliente.probar_conexion()
        if exito:
            print("✓ Conexión exitosa con Twilio")
        else:
            print("✗ No se pudo conectar con Twilio")
        return exito
    except Exception as e:
        print(f"✗ Error al probar conexión: {e}")
        return False


def test_enviar_sms_prueba(cliente: TwilioSMSClient):
    """Prueba 3: Enviar SMS de prueba"""
    print("\n" + "="*70)
    print("PRUEBA 3: Enviando SMS de prueba")
    print("="*70)
    
    if not cliente:
        print("✗ Cliente no disponible, saltando prueba")
        return False
    
    mensaje = "🧪 Prueba del módulo SMS de DriverApp Logs. Si recibes este mensaje, ¡todo funciona!"
    
    print(f"Mensaje ({len(mensaje)} chars):")
    print(f"  {mensaje}")
    print()
    
    try:
        exito = cliente.enviar_sms(mensaje)
        if exito:
            print("✓ SMS enviado exitosamente")
            print("  Revisa tu teléfono para confirmar la recepción")
        else:
            print("✗ No se pudo enviar el SMS")
        return exito
    except Exception as e:
        print(f"✗ Error al enviar SMS: {e}")
        return False


def test_notificador_con_errores():
    """Prueba 4: Probar notificador con datos simulados"""
    print("\n" + "="*70)
    print("PRUEBA 4: Probando notificador con errores simulados")
    print("="*70)
    
    # Simular resultado de procesar_aplicacion con errores NO controlados
    resultado_con_errores = {
        "app_name": "DriverApp GO2",
        "app_key": "driverapp_goto",
        "dia": date.today(),
        "fecha_str": date.today().isoformat(),
        "controlados_nuevos": [],
        "no_controlados_nuevos": [
            "ERROR - production - 2025-12-08 10:15:30 - SQL0911N The current transaction has been rolled back",
            "ERROR - production - 2025-12-08 10:16:45 - SQLSTATE[08001] Communication error detected",
            "ERROR - production - 2025-12-08 10:17:12 - Memory exhausted"
        ],
    }
    
    print("Datos simulados:")
    print(f"  App: {resultado_con_errores['app_name']}")
    print(f"  Errores NO controlados: {len(resultado_con_errores['no_controlados_nuevos'])}")
    print()
    
    try:
        enviar_sms_errores_no_controlados(resultado_con_errores)
        print("✓ Notificador ejecutado (revisa logs arriba para ver resultado)")
        return True
    except Exception as e:
        print(f"✗ Error al ejecutar notificador: {e}")
        return False


def test_notificador_sin_errores():
    """Prueba 5: Probar notificador sin errores (no debe enviar SMS)"""
    print("\n" + "="*70)
    print("PRUEBA 5: Probando notificador SIN errores (no debe enviar SMS)")
    print("="*70)
    
    resultado_sin_errores = {
        "app_name": "DriverApp GO2",
        "app_key": "driverapp_goto",
        "dia": date.today(),
        "fecha_str": date.today().isoformat(),
        "controlados_nuevos": [],
        "no_controlados_nuevos": [],  # Sin errores
    }
    
    print("Datos simulados:")
    print(f"  App: {resultado_sin_errores['app_name']}")
    print(f"  Errores NO controlados: {len(resultado_sin_errores['no_controlados_nuevos'])}")
    print()
    
    try:
        enviar_sms_errores_no_controlados(resultado_sin_errores)
        print("✓ Notificador ejecutado (no debería haber enviado SMS)")
        return True
    except Exception as e:
        print(f"✗ Error al ejecutar notificador: {e}")
        return False


def main():
    """Ejecuta todas las pruebas"""
    print("="*70)
    print("SUITE DE PRUEBAS - MÓDULO SMS TWILIO")
    print("="*70)
    print("\nEste script probará:")
    print("  1. Inicialización del cliente")
    print("  2. Conexión con Twilio")
    print("  3. Envío de SMS de prueba")
    print("  4. Notificador con errores simulados")
    print("  5. Notificador sin errores")
    
    input("\nPresiona ENTER para continuar...")
    
    # Ejecutar pruebas
    cliente = test_cliente_basico()
    
    if cliente and cliente.enabled:
        test_probar_conexion(cliente)
        
        respuesta = input("\n¿Deseas enviar un SMS de prueba real? (s/n): ")
        if respuesta.lower() == 's':
            test_enviar_sms_prueba(cliente)
    
    test_notificador_con_errores()
    test_notificador_sin_errores()
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    print("\n✅ Suite de pruebas completada")
    print("\nSi todo funcionó correctamente:")
    print("  1. El cliente se inicializó sin errores")
    print("  2. La conexión con Twilio fue exitosa")
    print("  3. Recibiste SMS de prueba (si lo autorizaste)")
    print("  4. Los logs muestran información detallada")
    print("\nSi hubo problemas, revisa:")
    print("  - Archivo .env tiene todas las variables de Twilio")
    print("  - Las credenciales son correctas")
    print("  - El número destino está verificado en Twilio (cuenta gratuita)")
    print("  - Instalaste twilio: pip install twilio")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
