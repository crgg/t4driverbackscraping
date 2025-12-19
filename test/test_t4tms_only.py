#!/usr/bin/env python3
"""
Script standalone para procesar solo T4TMS - BACKEND
Sin dependencia de base de datos PostgreSQL
"""

import os
import sys
from datetime import date, datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_app_credentials, get_app_urls
from app.session_manager import create_logged_session
from app.logs_scraper import fetch_logs_html, classify_logs, StaleLogsError

def main():
    app_key = "t4tms_backend"
    
    # Usar fecha de hoy
    dia = date.today()
    fecha_str = dia.isoformat()
    hora_actual = datetime.now().strftime("%I:%M:%S %p")
    
    print("=" * 70)
    print(f"TEST STANDALONE: T4TMS - BACKEND")
    print(f"Fecha: {fecha_str} {hora_actual}")
    print("=" * 70)
    
    try:
        # Obtener configuración
        app_name, username, password = get_app_credentials(app_key)
        base_url, login_url, logs_url = get_app_urls(app_key)
        
        print(f"\n📋 Configuración:")
        print(f"   App: {app_name}")
        print(f"   Base URL: {base_url}")
        print(f"   Logs URL: {logs_url}")
        print(f"   Usuario: {username}")
        print(f"   Password: {'*' * len(password) if password else 'NOT SET'}")
        
        # 1) Crear sesión autenticada
        print(f"\n{'='*70}")
        print("PASO 1: Autenticación")
        print("=" * 70)
        
        with create_logged_session(app_key) as session:
            print("✅ Sesión autenticada creada exitosamente")
            
            # 2) Obtener HTML de logs
            print(f"\n{'='*70}")
            print("PASO 2: Fetching logs HTML")
            print("=" * 70)
            
            html = fetch_logs_html(session, fecha_str, app_key)
            
            print(f"✓ HTML obtenido: {len(html)} bytes")
            
            # Guardar HTML para inspección
            debug_file = Path("t4tms_logs_debug.html")
            debug_file.write_text(html, encoding="utf-8")
            print(f"✓ HTML guardado en: {debug_file.absolute()}")
            
            # 3) Clasificar logs
            print(f"\n{'='*70}")
            print("PASO 3: Clasificación de logs")
            print("=" * 70)
            
            controlados, no_controlados = classify_logs(html)
            
            print(f"  • Errores controlados: {len(controlados)}")
            print(f"  • Errores NO controlados: {len(no_controlados)}")
            
            # 4) Guardar resultados
            print(f"\n{'='*70}")
            print("PASO 4: Guardando resultados")
            print("=" * 70)
            
            output_dir = Path("salida_logs_t4tms_test")
            output_dir.mkdir(exist_ok=True)
            
            # Guardar controlados
            if controlados:
                controlados_file = output_dir / f"controlados_{fecha_str}.txt"
                controlados_file.write_text("\n".join(controlados), encoding="utf-8")
                print(f"✓ Controlados guardados en: {controlados_file}")
                print(f"   Primeros 3 errores:")
                for i, error in enumerate(controlados[:3], 1):
                    print(f"   {i}. {error[:100]}...")
            else:
                print("✓ No hay errores controlados")
            
            # Guardar no controlados
            if no_controlados:
                no_controlados_file = output_dir / f"no_controlados_{fecha_str}.txt"
                no_controlados_file.write_text("\n".join(no_controlados), encoding="utf-8")
                print(f"✓ NO controlados guardados en: {no_controlados_file}")
                print(f"   Primeros 3 errores:")
                for i, error in enumerate(no_controlados[:3], 1):
                    print(f"   {i}. {error[:100]}...")
            else:
                print("✓ No hay errores NO controlados")
        
        print(f"\n{'='*70}")
        print("✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"\nArchivos generados:")
        print(f"  - {debug_file.absolute()}")
        print(f"  - {output_dir.absolute()}")
        
    except StaleLogsError as e:
        print(f"\n{'='*70}")
        print("🚨 LOGS DESACTUALIZADOS")
        print("=" * 70)
        print(f"App: {app_key}")
        print(f"Fecha solicitada: {e.fecha_str}")
        print(f"Log más reciente: {e.most_recent_date}")
        print(f"Días de antigüedad: {e.days_old}")
        print(f"\nMensaje: {str(e)}")
        sys.exit(2)
        
    except Exception as e:
        print(f"\n{'='*70}")
        print("❌ ERROR")
        print("=" * 70)
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print(f"\nTraceback completo:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
