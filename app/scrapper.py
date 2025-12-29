# app/scraper.py
from datetime import date
from pathlib import Path
from typing import Any, Dict

from app.config import get_app_credentials
from app.session_manager import create_logged_session
from app.logs_scraper import fetch_logs_html, classify_logs
from app.writer import save_logs
from app.error_filter import dividir_nuevos_y_avisados


def procesar_aplicacion(app_key: str, fecha_str: str, dia: date) -> Dict[str, Any]:
    """
    Hace el scraping, clasificación y guardado de logs
    para una aplicación, PERO NO ENVÍA CORREOS.

    Devuelve un dict con info útil (app_name, etc.).
    """
    app_name, _, _ = get_app_credentials(app_key)

    print(f"\n{'='*70}")
    print(f"Procesando: {app_name}")
    print(f"{'='*70}")

    # 1) Scrapping de logs
    with create_logged_session(app_key) as session:
        html = fetch_logs_html(session, fecha_str, app_key)

        # DEBUG - Guardar HTML de debug (con sufijo de app para diferenciarlo)
        # debug_file = f"debug_logs_{app_key}.html"
        # try:
        #     Path(debug_file).write_text(html, encoding="utf-8")
        #     print(f"✓ HTML guardado en {debug_file}")
        # except Exception as e:
        #     print(f"Error saving debug file: {e}")

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

    # Metrícas de volumen
    log_size_kb = len(html.encode('utf-8')) / 1024
    log_lines = html.count('\n')
    print(f"  • Volumen de logs: {log_size_kb:.2f} KB ({log_lines} líneas)")

    # 3) Guardar SOLO los nuevos
    save_logs(
        controlados_nuevos,
        no_controlados_nuevos,
        mode="w",
        app_key=app_key,
    )
    print("✓ Logs guardados en carpeta 'salida_logs' (solo nuevos)")

    # 4) Guardar Historial Global (Error History Module)
    # Solo nos interesan los NO controlados para este historial crítico
    # Intentamos guardar TANTO los nuevos como los avisados.
    # La BD se encarga de ignorar duplicados (ON CONFLICT DO NOTHING).
    todos_no_controlados = no_controlados_nuevos + no_controlados_avisados
    
    if todos_no_controlados:
        try:
            from db.error_history import insert_error_history, init_error_history_db
            import re
            from datetime import datetime
            
            # Asegurar que la tabla existe (idempotente)
            init_error_history_db()
            
            count_hist = 0
            # Regex común para: "2025-12-29 11:12:39"
            date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
            
            for error_str in todos_no_controlados:
                # Intentar extraer fecha real del texto
                match = date_pattern.search(error_str)
                timestamp = None
                if match:
                    try:
                        timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass # Usar default NOW() si falla parsing
                
                insert_error_history(app_name, error_str, timestamp)
                count_hist += 1
            print(f"✓ Historial actualizado: {count_hist} errores procesados para deduplicación")
        except Exception as e_hist:
            print(f"⚠️ Error al guardar historial: {e_hist}")

    return {
        "app_key": app_key,
        "app_name": app_name,
        "dia": dia,
        "fecha_str": fecha_str,
        "controlados_nuevos": controlados_nuevos,
        "controlados_avisados": controlados_avisados,
        "no_controlados_nuevos": no_controlados_nuevos,
        "no_controlados_avisados": no_controlados_avisados,
    }
