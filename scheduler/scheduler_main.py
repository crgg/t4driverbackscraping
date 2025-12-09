# scheduler/scheduler_main.py
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from config import INTERVAL, ENV
from utils import get_logger, run_main_script, mark_success

logger = get_logger()

print("Comenzando envio de correos automatizado, espera un poco . . .")

def job():
    try:
        logger.info("Ejecutando job: main.py")
        run_main_script(logger)   # 👈 AQUÍ el cambio importante ✅
        mark_success()
        logger.info("Job ejecutado correctamente")
    except Exception as e:
        logger.exception(f"Error al ejecutar job: {e}")

if __name__ == "__main__":
    logger.info(f"Iniciando scheduler en modo '{ENV}' con intervalo {INTERVAL}")

    # 👇 PRIMERA EJECUCIÓN INMEDIATA
    job()

    print(f"Primer correo enviado, el proximo se enviara segun el intervalo configurado: {INTERVAL}")
    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", id="ejecutar_main", **INTERVAL)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler detenido por el usuario")
