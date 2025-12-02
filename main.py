# main.py
import sys
from pathlib import Path
from datetime import date

from app.config import APPS_CONFIG, get_app_credentials
from app.session_manager import create_logged_session
from app.logs_scraper import fetch_logs_html, classify_logs
from app.writer import save_logs
from app.email_notifier import enviar_resumen_por_correo

def procesar_aplicacion(app_key: str, fecha_str: str, dia: date) -> None:
    """
    Procesa el scrapping, clasificación y envío de correo para una aplicación.
    
    Args:
        app_key: clave de la aplicación en APPS_CONFIG
        fecha_str: fecha en formato "YYYY-MM-DD"
        dia: objeto date para reportes
    """
    try:
        app_name, _, _ = get_app_credentials(app_key)
        
        print(f"\n{'='*70}")
        print(f"Procesando: {app_name}")
        print(f"{'='*70}")
        
        with create_logged_session(app_key) as session:
            html = fetch_logs_html(session, fecha_str, app_key)
            
            # Guardar HTML de debug (con sufijo de app para diferenciarlo)
            debug_file = f"debug_logs_{app_key}.html"
            Path(debug_file).write_text(html, encoding="utf-8")
            print(f"✓ HTML guardado en {debug_file}")
            
            controlados, no_controlados = classify_logs(html)
        
        print(f"  • Errores controlados: {len(controlados)}")
        print(f"  • Errores NO controlados: {len(no_controlados)}")
        
        # Guardar los logs de esta ejecución sobrescribiendo archivos previos
        save_logs(controlados, no_controlados, mode="w", app_key=app_key)
        print(f"✓ Logs guardados en carpeta 'salida_logs'")
        
        # Enviar correo con el nombre dinámico de la aplicación
        enviar_resumen_por_correo(dia, app_name, app_key)
        print(f"✓ Correo enviado para {app_name}")
        
    except Exception as e:
        print(f"❌ Error procesando {app_name}: {e}")
        raise


def main():
    # Fecha por parámetro: python main.py 2025-11-26
    if len(sys.argv) >= 2:
        fecha_str = sys.argv[1]
        dia = date.fromisoformat(fecha_str)
    else:
        dia = date.today()
        fecha_str = dia.isoformat()

    print(f"📅 Fecha de reporte: {fecha_str}")
    print(f"📧 Procesando {len(APPS_CONFIG)} aplicaciones...\n")

    # Procesar cada aplicación
    for app_key in APPS_CONFIG.keys():
        procesar_aplicacion(app_key, fecha_str, dia)
    
    print(f"\n{'='*70}")
    print(f"✅ Scrapping completado para todas las aplicaciones")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
