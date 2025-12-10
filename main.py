# main.py
import os
import sys
from datetime import date

from app.config import APPS_CONFIG
from db import (
    init_db,
    reset_all_alerted_errors,
    reset_alerted_errors_for_date,
)
from app.scrapper import procesar_aplicacion
from app.notifier import notificar_app


def resolver_fecha() -> tuple[str, date]:
    """
    Toma los argumentos de línea de comandos (sys.argv)
    y decide qué fecha usar.
    Si hay un argumento, usa ese (YYYY-MM-DD).
    Si no, usa la fecha de hoy.
    """
    if len(sys.argv) >= 2:
        fecha_str = sys.argv[1]
        dia = date.fromisoformat(fecha_str)
    else:
        dia = date.today()
        fecha_str = dia.isoformat()
    return fecha_str, dia


def aplicar_resets(dia: date, fecha_str: str) -> None:
    """
    Aplica la lógica de reset de memoria según variables de entorno.
    """
    if os.getenv("RESET_ALERTED_ERRORS_ALL") == "1":
        reset_all_alerted_errors()
        print("⚠️ RESET_ALERTED_ERRORS_ALL=1 → TRUNCATE TABLE alerted_errors (se borra TODO)")
    elif os.getenv("RESET_ALERTED_ERRORS_FOR_DATE") == "1":
        reset_alerted_errors_for_date(dia)
        print(f"⚠️ RESET_ALERTED_ERRORS_FOR_DATE=1 → borrar registros de fecha {fecha_str} en alerted_errors")

def main() -> None:
    # 1) Inicializar la base de datos
    init_db()

    # 2) Resolver fecha usando sys.argv (como antes)
    fecha_str, dia = resolver_fecha()

    # 3) Aplicar resets (si corresponde)
    aplicar_resets(dia, fecha_str)

    print(f"📅 Fecha de reporte: {fecha_str}")
    print(f"📧 Procesando {len(APPS_CONFIG)} aplicaciones...\n")

    # 4) Scraping + clasificación + guardado
    resultados = []
    for app_key in APPS_CONFIG.keys():
        resultado = procesar_aplicacion(app_key, fecha_str, dia)
        resultados.append(resultado)

    # 5) Envío de correos (notificaciones)
    for resultado in resultados:
        notificar_app(resultado)

    print(f"\n{'='*70}")
    print("✅ Scrapping completado para todas las aplicaciones")
    
    # Mostrar número de destino SMS
    twilio_number = os.getenv("TWILIO_TO_NUMBER")
    if twilio_number:
        print(f"📱 SMS enviados al número: {twilio_number}")
        
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
