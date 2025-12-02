# main.py
import os
import sys
from datetime import date
from pathlib import Path

from app.config import APPS_CONFIG, get_app_credentials
from app.session_manager import create_logged_session
from app.logs_scraper import fetch_logs_html, classify_logs
from app.writer import save_logs
from app.email_notifier import enviar_resumen_por_correo

from db import (
    init_db,
    reset_all_alerted_errors,
    reset_alerted_errors_for_date,
)
from app.error_filter import dividir_nuevos_y_avisados


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
        
        # 1) Scrapping de logs
        with create_logged_session(app_key) as session:
            html = fetch_logs_html(session, fecha_str, app_key)
            
            # Guardar HTML de debug (con sufijo de app para diferenciarlo)
            debug_file = f"debug_logs_{app_key}.html"
            Path(debug_file).write_text(html, encoding="utf-8")
            print(f"✓ HTML guardado en {debug_file}")
            
            controlados, no_controlados = classify_logs(html)

        # 2) Separar en NUEVOS vs AVISADOS usando la BD
        controlados_nuevos, controlados_avisados = dividir_nuevos_y_avisados(
            controlados, app_key, dia, "controlado"
        )
        no_controlados_nuevos, no_controlados_avisados = dividir_nuevos_y_avisados(
            no_controlados, app_key, dia, "no_controlado"
        )

        print(f"  • Errores controlados nuevos: {len(controlados_nuevos)}")
        print(f"  • Errores controlados avisados antes: {len(controlados_avisados)}")
        print(f"  • Errores NO controlados nuevos: {len(no_controlados_nuevos)}")
        print(f"  • Errores NO controlados avisados antes: {len(no_controlados_avisados)}")
        
        # 3) Guardar SOLO los nuevos, para que el resumen del correo
        #    sea de lo recién aparecido desde la última ejecución
        save_logs(
            controlados_nuevos,
            no_controlados_nuevos,
            mode="w",
            app_key=app_key,
        )
        print("✓ Logs guardados en carpeta 'salida_logs' (solo nuevos)")
        
        # 4) Enviar correo con el nombre dinámico de la aplicación
        enviar_resumen_por_correo(dia, app_name, app_key)
        print(f"✓ Correo enviado para {app_name}")
        
    except Exception as e:
        print(f"❌ Error procesando {app_name}: {e}")
        raise


def main():
    # Inicializar la base de datos (crear tabla si no existe)
    init_db()

    # Fecha por parámetro: python main.py 2025-11-26
    if len(sys.argv) >= 2:
        fecha_str = sys.argv[1]
        dia = date.fromisoformat(fecha_str)
    else:
        dia = date.today()
        fecha_str = dia.isoformat()

    # 🔴 LÓGICA DE RESET DE MEMORIA (opcional, vía variables de entorno)

    # 1) Reset TOTAL de todos los avisos (todas las fechas, todas las apps)
    #    Ejecución:
    #    RESET_ALERTED_ERRORS_ALL=1 python main.py
    if os.getenv("RESET_ALERTED_ERRORS_ALL") == "1":
        reset_all_alerted_errors()
        print("⚠️ RESET_ALERTED_ERRORS_ALL=1 → TRUNCATE TABLE alerted_errors (se borra TODO)")

    # 2) Reset SOLO de la fecha que se está procesando (dia)
    #    Ejecución:
    #    RESET_ALERTED_ERRORS_FOR_DATE=1 python main.py 2025-12-02
    elif os.getenv("RESET_ALERTED_ERRORS_FOR_DATE") == "1":
        reset_alerted_errors_for_date(dia)
        print(f"⚠️ RESET_ALERTED_ERRORS_FOR_DATE=1 → borrar registros de fecha {fecha_str} en alerted_errors")

    print(f"📅 Fecha de reporte: {fecha_str}")
    print(f"📧 Procesando {len(APPS_CONFIG)} aplicaciones...\n")

    # Procesar cada aplicación
    for app_key in APPS_CONFIG.keys():
        procesar_aplicacion(app_key, fecha_str, dia)
    
    print(f"\n{'='*70}")
    print("✅ Scrapping completado para todas las aplicaciones")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
