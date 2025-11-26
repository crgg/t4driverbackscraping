# app/config.py
import os
from dotenv import load_dotenv  # 👈 nuevo import

# Cargar variables desde .env
load_dotenv()

# URLs base
BASE_URL = "https://driverapp.goto-logistics.com"
LOGIN_PATH = "/login"
LOGS_PATH = "/logs"

# Credenciales leídas desde .env
USERNAME = os.getenv("DRIVERAPP_USER")
PASSWORD = os.getenv("DRIVERAPP_PASS")

# Palabras clave para detectar errores NO controlados
KEYWORDS_NO_CONTROLADO = [
    "sqlstate",
    "exception",
    "pdoexception",
]

# (Opcional) pequeña comprobación
if not USERNAME or not PASSWORD:
    raise RuntimeError("Faltan DRIVERAPP_USER o DRIVERAPP_PASS en el archivo .env")
