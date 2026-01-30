# scheduler/config.py
from pathlib import Path
import os

# Carpeta raíz del proyecto (donde está main.py)
BASE_DIR = Path(__file__).resolve().parents[1]

# Ruta a main.py
MAIN_PATH = BASE_DIR / "main.py"

# Carpeta y archivos de logs
# Carpeta donde esta este archivo (scheduler)
SCHEDULER_DIR = Path(__file__).resolve().parent

SCHEDULER_LOG_FILE = SCHEDULER_DIR / "scheduler.log"
HEALTH_FILE = SCHEDULER_DIR / "last_success.txt"

# === Entorno: test o prod ===
# Por defecto: "test". Para producción, exporta SCHED_ENV=prod
ENV = os.getenv("SCHED_ENV", "test").lower()

# Intervalos según entorno
# test  -> cada 1 minuto
# prod  -> cada 4 horas
if ENV == "prod":
    INTERVAL = {"hours": 7}
else:
    INTERVAL = {"minutes": 1}
