# app/config.py
import os
from dotenv import load_dotenv
from typing import Dict, List

# Cargar variables desde .env
load_dotenv()

# Palabras clave para detectar errores NO controlados
KEYWORDS_NO_CONTROLADO = [
    "sqlstate",
    "exception",
    "pdoexception",
]

# === CONFIGURACIÓN DE MÚLTIPLES APLICACIONES ===
# Estructura: {clave_aplicacion: {config_dict}}
APPS_CONFIG: Dict[str, Dict] = {
    "driverapp_goto": {
        "name": "DriverApp GoTo Logistics",
        "base_url": "https://driverapp.goto-logistics.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "DRIVERAPP_USER",
        "password_env": "DRIVERAPP_PASS",
    },
    "goexperior": {
        "name": "GoExperior",
        "base_url": "https://driverapp.goexperior.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "GOEXPERIOR_USER",
        "password_env": "GOEXPERIOR_PASS",
    },
    "klc": {
        "name": "KLC T4App",
        "base_url": "https://klc.t4app.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "KLC_USER",
        "password_env": "KLC_PASS",
    },
    "accuratecargo": {
        "name": "AccurateCargo T4App",
        "base_url": "https://accuratecargo.t4app.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "ACCURATECARGO_USER",
        "password_env": "ACCURATECARGO_PASS",
    },
}


def get_app_credentials(app_key: str) -> tuple[str, str, str]:
    """
    Obtiene las credenciales y nombre de una aplicación.
    
    Args:
        app_key: clave en APPS_CONFIG (ej: 'driverapp_goto')
    
    Returns:
        (app_name, username, password)
    
    Raises:
        RuntimeError: si faltan credenciales
    """
    if app_key not in APPS_CONFIG:
        raise ValueError(f"Aplicación '{app_key}' no encontrada en APPS_CONFIG")
    
    config = APPS_CONFIG[app_key]
    app_name = config["name"]
    username = os.getenv(config["username_env"])
    password = os.getenv(config["password_env"])
    
    if not username or not password:
        raise RuntimeError(
            f"Faltan credenciales para {app_name}. "
            f"Verifica {config['username_env']} y {config['password_env']} en .env"
        )
    
    return app_name, username, password


def get_app_urls(app_key: str) -> tuple[str, str, str]:
    """
    Obtiene las URLs de una aplicación.
    
    Args:
        app_key: clave en APPS_CONFIG
    
    Returns:
        (base_url, login_url, logs_url)
    """
    if app_key not in APPS_CONFIG:
        raise ValueError(f"Aplicación '{app_key}' no encontrada en APPS_CONFIG")
    
    config = APPS_CONFIG[app_key]
    base_url = config["base_url"]
    login_url = base_url + config["login_path"]
    logs_url = base_url + config["logs_path"]
    
    return base_url, login_url, logs_url


# === RETROCOMPATIBILIDAD (para código existente) ===
# Si algo todavía usa estas variables, las asignamos desde la config de GoTo
USERNAME = os.getenv("DRIVERAPP_USER")
PASSWORD = os.getenv("DRIVERAPP_PASS")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Faltan DRIVERAPP_USER o DRIVERAPP_PASS en el archivo .env")