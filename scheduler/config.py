# scheduler/config.py
from pathlib import Path
import os

# Carpeta raíz del proyecto (donde está main.py)
BASE_DIR = Path(__file__).resolve().parents[1]

# Ruta a main.py
MAIN_PATH = BASE_DIR / "main.py"

# Carpeta y archivos de logs
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

SCHEDULER_LOG_FILE = LOG_DIR / "scheduler.log"
HEALTH_FILE = LOG_DIR / "last_success.txt"

# === Entorno: test o prod ===
# Por defecto: "test". Para producción, exporta SCHED_ENV=prod
ENV = os.getenv("SCHED_ENV", "test").lower()

# Intervalos según entorno
# test  -> cada 1 minuto
# prod  -> cada 4 horas
if ENV == "prod":
    INTERVAL = {"hours": 4}
else:
    INTERVAL = {"minutes": 1}
