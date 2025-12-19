# main.py
import os
import sys
from datetime import date, datetime

from app.config import APPS_CONFIG
from db import (
    init_db,
    reset_all_alerted_errors,
    reset_alerted_errors_for_date,
)
from app.scrapper import procesar_aplicacion
from app.notifier import notificar_app, notificar_fecha_futura, notificar_logs_desactualizados
from app.logs_scraper import StaleLogsError
from app.config import APPS_CONFIG


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

    # Obtener hora actual de ejecución
    hora_actual = datetime.now().strftime("%I:%M:%S %p")
    
    print(f"📅 Fecha y hora de reporte: {fecha_str} {hora_actual}")
    print(f"📧 Procesando {len(APPS_CONFIG)} aplicaciones...\n")

    # 4) Scraping + clasificación + guardado
    resultados = []
    errores = []  # Rastrear aplicaciones con errores
    
    for app_key in APPS_CONFIG.keys():
        try:
            resultado = procesar_aplicacion(app_key, fecha_str, dia)
            resultados.append(resultado)
            
        except RuntimeError as e:
            msg = str(e)
            if "No se puede procesar fecha futura" in msg:
                 app_name = APPS_CONFIG.get(app_key, {}).get('name', app_key)
                 print(f"⚠️ {app_name}: Fecha futura detectada ({fecha_str}). Enviando notificaciones...")
                 notificar_fecha_futura(app_key, app_name, fecha_str)
                 # No lo agregamos a 'errores' para no ensuciar el reporte final de errores críticos
                 continue
            else:
                 raise e  # Re-lanzar para que lo capture el Exception genérico
        
        except StaleLogsError as e:
            # Logs desactualizados (2+ días sin actualizar)
            app_name_stale = APPS_CONFIG.get(app_key, {}).get('name', app_key)
            print(f"🚨 {app_name_stale}: STALE LOGS - {e.days_old} days old (most recent: {e.most_recent_date})")
            print(f"   Enviando alertas de peligro y continuando con las demás aplicaciones...")
            
            # Enviar notificaciones de peligro
            notificar_logs_desactualizados(
                app_key=e.app_key,
                app_name=app_name_stale,
                fecha_str=e.fecha_str,
                days_old=e.days_old,
                most_recent_date=str(e.most_recent_date)
            )
            
            # No agregamos a 'errores' porque las notificaciones ya se enviaron
            continue
            
        except Exception as e:
            # Registrar el error pero continuar con las demás aplicaciones
            app_name_error = APPS_CONFIG.get(app_key, {}).get('name', app_key)
            error_info = {
                'app_key': app_key,
                'app_name': app_name_error,
                'error_type': type(e).__name__,
                'error_msg': str(e)
            }
            errores.append(error_info)
            print(f"⚠️ Error al procesar {app_name_error}: {type(e).__name__}")
            print(f"   Continuando con las demás aplicaciones...\n")

    # 5) Envío de correos (notificaciones) - solo para aplicaciones exitosas
    for resultado in resultados:
        try:
            notificar_app(resultado)
        except Exception as e:
            app_name = resultado.get('app_name', 'Desconocida')
            print(f"⚠️ Error al notificar {app_name}: {type(e).__name__} - {str(e)}")

    print(f"\n{'='*70}")
    print("✅ Scrapping completado para todas las aplicaciones")
    
    # Mostrar resumen de éxito/errores
    if resultados:
        print(f"✓ Aplicaciones procesadas exitosamente: {len(resultados)}/{len(APPS_CONFIG)}")
    
    if errores:
        print(f"\n⚠️ Aplicaciones con errores: {len(errores)}")
        for error in errores:
            print(f"   • {error['app_name']}: {error['error_type']}")
            if 'Connection' in error['error_type'] or 'Timeout' in error['error_type']:
                print(f"     → Problema de conectividad: {error['error_msg'][:100]}")
    
    # Mostrar número de destino SMS
    twilio_number = os.getenv("TWILIO_TO_NUMBER")
    if twilio_number:
        print(f"\n📱 SMS enviados al número: {twilio_number}")
        
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
