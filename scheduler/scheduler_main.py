# scheduler/scheduler_main.py
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

from dotenv import load_dotenv  # 👈 nuevo
load_dotenv()                   # 👈 carga las variables de .env

from config import INTERVAL, ENV
from utils import get_logger, run_main_script, mark_success

logger = get_logger()

print("Comenzando envio de correos automatizado, espera un poco . . .")

def job():
    """Job que se ejecuta según el intervalo definido en config.INTERVAL."""
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Disparando job en modo '{ENV}' a las {ahora}")

    try:
        run_main_script(logger)
        mark_success()
    except Exception as e:
        logger.exception(f"Error al ejecutar job: {e}")

if __name__ == "__main__":
    logger.info(f"Iniciando scheduler en modo '{ENV}' con intervalo {INTERVAL}")

    scheduler = BlockingScheduler()
    # interval = cada X tiempo (X está en INTERVAL)
    scheduler.add_job(job, "interval", id="ejecutar_main", **INTERVAL)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler detenido por el usuario")
