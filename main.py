# t4alerts_automation/main.py
import os
import sys
from datetime import date, datetime

# Ensure the root directory is in sys.path to find shared modules (app, db, sms, etc.)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.config import get_apps_config
from db import (
    init_db,
    reset_all_alerted_errors,
    reset_alerted_errors_for_date,
)
from app.scrapper import procesar_aplicacion
from app.notifier import notificar_app, notificar_fecha_futura, notificar_logs_desactualizados
from app.logs_scraper import StaleLogsError


def resolver_fecha() -> tuple[str, date]:
    """
    Toma los argumentos de línea de comandos (sys.argv)
    y decide qué fecha usar.
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
    # 1) Contexto de aplicación (opcional pero recomendado para cargar apps de DB)
    apps_config = {}
    try:
        # Intentamos cargar el contexto para acceder a MonitoredApp
        from t4alerts_backend.app import create_app
        flask_app = create_app()
        with flask_app.app_context():
            apps_config = get_apps_config(dynamic_only=False)
    except Exception as e:
        print(f"⚠️ Info: Running without Flask context. Attempting static loading fallback.")
        # Fallback to static config from app.config
        try:
            from app.config import get_apps_config
            apps_config = get_apps_config(dynamic_only=False)
        except:
            from app.config import APPS_CONFIG_LEGACY
            apps_config = APPS_CONFIG_LEGACY

    # 2) Inicializar la base de datos de alertas
    init_db()

    # 3) Resolver fecha
    fecha_str, dia = resolver_fecha()

    # 4) Aplicar resets
    aplicar_resets(dia, fecha_str)

    # Obtener hora actual de ejecución
    hora_actual = datetime.now().strftime("%I:%M:%S %p")
    
    print(f"📅 Fecha y hora de reporte: {fecha_str} {hora_actual}")
    print(f"📧 Procesando {len(apps_config)} aplicaciones...\n")

    # 5) Scraping + clasificación + guardado
    resultados = []
    errores = []
    
    for app_key in apps_config.keys():
        try:
            # Procesar aplicación
            # NOTA: procesar_aplicacion usa internamente get_app_credentials que ahora es dinámico
            # pero como ya cargamos apps_config aquí, podríamos pasarlo o dejar que use su fallback.
            # Para mayor robustez, nos aseguramos de que el contexto de Flask esté activo si es posible.
            
            # Si tenemos flask_app, lo usamos para cada aplicación por si hay consultas a BD internas
            if 'flask_app' in locals():
                with flask_app.app_context():
                    resultado = procesar_aplicacion(app_key, fecha_str, dia)
            else:
                resultado = procesar_aplicacion(app_key, fecha_str, dia)
                
            resultados.append(resultado)
            
        except RuntimeError as e:
            msg = str(e)
            if "No se puede procesar fecha futura" in msg:
                 app_name = apps_config.get(app_key, {}).get('name', app_key)
                 print(f"⚠️ {app_name}: Fecha futura detectada ({fecha_str}). Enviando notificaciones...")
                 notificar_fecha_futura(app_key, app_name, fecha_str)
                 continue
            else:
                 raise e
        
        except StaleLogsError as e:
            app_name_stale = apps_config.get(app_key, {}).get('name', app_key)
            print(f"🚨 {app_name_stale}: STALE LOGS - {e.days_old} days old")
            notificar_logs_desactualizados(
                app_key=e.app_key,
                app_name=app_name_stale,
                fecha_str=e.fecha_str,
                days_old=e.days_old,
                most_recent_date=str(e.most_recent_date)
            )
            continue
            
        except Exception as e:
            app_name_error = apps_config.get(app_key, {}).get('name', app_key)
            error_info = {
                'app_key': app_key,
                'app_name': app_name_error,
                'error_type': type(e).__name__,
                'error_msg': str(e)
            }
            errores.append(error_info)
            print(f"⚠️ Error al procesar {app_name_error}: {type(e).__name__} - {e}")
            print(f"   Continuando con las demás aplicaciones...\n")

    # 6) Envío de correos
    for resultado in resultados:
        try:
            notificar_app(resultado)
        except Exception as e:
            app_name = resultado.get('app_name', 'Desconocida')
            print(f"⚠️ Error al notificar {app_name}: {e}")

    print(f"\n{'='*70}")
    print("✅ Scrapping completado para todas las aplicaciones")
    
    if resultados:
        print(f"✓ Aplicaciones procesadas exitosamente: {len(resultados)}/{len(apps_config)}")
    
    if errores:
        print(f"\n⚠️ Aplicaciones con errores: {len(errores)}")
        for error in errores:
            print(f"   • {error['app_name']}: {error['error_type']}")
    
    # Twilio
    twilio_number = os.getenv("TWILIO_TO_NUMBER")
    if twilio_number:
        print(f"\n📱 SMS enviados al número: {twilio_number}")
        
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
