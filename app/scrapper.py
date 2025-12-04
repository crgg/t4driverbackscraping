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
        # Path(debug_file).write_text(html, encoding="utf-8")
        # print(f"✓ HTML guardado en {debug_file}")

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

    # 3) Guardar SOLO los nuevos
    save_logs(
        controlados_nuevos,
        no_controlados_nuevos,
        mode="w",
        app_key=app_key,
    )
    print("✓ Logs guardados en carpeta 'salida_logs' (solo nuevos)")

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
