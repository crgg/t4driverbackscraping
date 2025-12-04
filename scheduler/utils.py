# scheduler/utils.py
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import subprocess
import sys

from config import (
    SCHEDULER_LOG_FILE,
    HEALTH_FILE,
    MAIN_PATH,
    BASE_DIR,
)

def get_logger() -> logging.Logger:
    """Configura y devuelve un logger con rotación de archivo."""
    logger = logging.getLogger("scheduler")

    # Evita añadir handlers duplicados si se llama varias veces
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        SCHEDULER_LOG_FILE,
        maxBytes=1_000_000,  # 1 MB
        backupCount=5,       # guarda hasta 5 versiones antiguas
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def run_main_script(logger: logging.Logger) -> None:
    """Ejecuta main.py como si hicieras 'python main.py' en la raíz del proyecto."""
    logger.info("Lanzando main.py desde scheduler")

    subprocess.run(
        [sys.executable, str(MAIN_PATH)],
        check=True,
        cwd=str(BASE_DIR),  # para que main.py se ejecute en scrapping_project
    )

    logger.info("main.py terminó correctamente")


def mark_success() -> None:
    """Guarda la fecha/hora de la última ejecución correcta."""
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with HEALTH_FILE.open("w", encoding="utf-8") as f:
        f.write(f"Última ejecución correcta: {ahora}\n")
