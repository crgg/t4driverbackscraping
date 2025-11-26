# main.py
import sys
from pathlib import Path
from datetime import date

from app.session_manager import create_logged_session
from app.logs_scraper import fetch_logs_html, classify_logs
from app.writer import save_logs
from app.email_notifier import enviar_resumen_por_correo


def main():
    # Fecha por parámetro: python main.py 2025-11-26
    if len(sys.argv) >= 2:
        # viene como string, por ejemplo "2025-11-26"
        fecha_str = sys.argv[1]
        # lo convertimos a date para el correo / estadísticas
        dia = date.fromisoformat(fecha_str)
    else:
        # Si no pasas nada, usa la fecha de hoy
        dia = date.today()
        fecha_str = dia.isoformat()

    print(f"Usando fecha: {fecha_str}")

    with create_logged_session() as session:
        html = fetch_logs_html(session, fecha_str)

        Path("debug_logs.html").write_text(html, encoding="utf-8")
        print("He guardado el HTML en debug_logs.html")

        controlados, no_controlados = classify_logs(html)

    print(f"Errores controlados: {len(controlados)}")
    print(f"Errores NO controlados: {len(no_controlados)}")

    save_logs(controlados, no_controlados)
    print("Logs guardados en carpeta 'salida_logs'")

    # === NUEVO: enviar el resumen por correo (usa 'dia', que es date) ===
    enviar_resumen_por_correo(dia)


if __name__ == "__main__":
    main()
