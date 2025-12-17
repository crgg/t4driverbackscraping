#!/usr/bin/env python3
# test_klc_crossdock.py
"""
Script de prueba para KLC Crossdock
Consulta los logs de una fecha específica (2025-09-12) y envía notificaciones.
"""
from datetime import date

from db import init_db
from app.scrapper import procesar_aplicacion
from app.notifier import notificar_app

def main():
    print("="*70)
    print("🧪 TEST: KLC Crossdock - Fecha 2025-09-12")
    print("="*70)
    
    # Inicializar base de datos
    init_db()
    
    # Configuración del test
    app_key = "klc_crossdock"
    fecha_str = "2025-09-12"
    dia = date.fromisoformat(fecha_str)
    
    print(f"\n📅 Consultando logs de: {fecha_str}")
    print(f"🏢 Aplicación: KLC Crossdock T4App\n")
    
    try:
        # 1. Scraping y clasificación
        print("🔍 Iniciando scraping...")
        resultado = procesar_aplicacion(app_key, fecha_str, dia)
        
        # Mostrar resumen
        print(f"\n{'='*70}")
        print("📊 RESUMEN DE ERRORES DETECTADOS")
        print(f"{'='*70}")
        
        no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
        controlados_nuevos = resultado.get("controlados_nuevos", [])
        
        print(f"❌ Errores NO controlados (nuevos): {len(no_controlados_nuevos)}")
        print(f"⚠️  Errores controlados (nuevos): {len(controlados_nuevos)}")
        
        if no_controlados_nuevos:
            print(f"\n🔴 Primeros 3 errores NO controlados:")
            for i, error in enumerate(no_controlados_nuevos[:3], 1):
                preview = error[:100] + "..." if len(error) > 100 else error
                print(f"   {i}. {preview}")
        
        # 2. Enviar notificaciones
        print(f"\n{'='*70}")
        print("📧 ENVIANDO NOTIFICACIONES")
        print(f"{'='*70}\n")
        
        if no_controlados_nuevos:
            print("📬 Enviando notificaciones...")
            notificar_app(resultado)
            
            print("\n✅ Notificaciones enviadas:")
            print("   • Email: [T4APP - KLC CROSSDOCK] Errors 2025-09-12")
            print("   • SMS: Mensaje conciso con conteo de errores")
            print("   • Slack: Notificación al canal configurado")
        else:
            print("ℹ️  No hay errores NO controlados, no se envían notificaciones")
        
        print(f"\n{'='*70}")
        print("✅ TEST COMPLETADO")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR durante el test:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        print(f"\n{'='*70}\n")
        raise

if __name__ == "__main__":
    main()
