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

# LEGACY: Hardcoded configuration (used as fallback)
# Comentado para que la lista inicie vacía y se llene dinámicamente desde Custom Scan
APPS_CONFIG_LEGACY: Dict[str, Dict] = {
    # "driverapp_goto": {
    #     "name": "DRIVERAPP - GO 2 LOGISTICS",
    #     "base_url": "https://driverapp.goto-logistics.com",
    #     "login_path": "/login",
    #     "logs_path": "/logs",
    #     "username_env": "DRIVERAPP_USER",
    #     "password_env": "DRIVERAPP_PASS",
    # },
    # "goexperior": {
    #     "name": "DRIVERAPP - GOEXPERIOR",
    #     "base_url": "https://driverapp.goexperior.com",
    #     "login_path": "/login",
    #     "logs_path": "/logs",
    #     "username_env": "GOEXPERIOR_USER",
    #     "password_env": "GOEXPERIOR_PASS",
    # },
    # "klc": {
    #     "name": "T4APP - KLC",
    #     "base_url": "https://klc.t4app.com",
    #     "login_path": "/login",
    #     "logs_path": "/logs",
    #     "username_env": "KLC_USER",
    #     "password_env": "KLC_PASS",
    # },
    # "accuratecargo": {
    #     "name": "T4APP - ACCURATECARGO",
    #     "base_url": "https://accuratecargo.t4app.com",
    #     "login_path": "/login",
    #     "logs_path": "/logs",
    #     "username_env": "ACCURATECARGO_USER",
    #     "password_env": "ACCURATECARGO_PASS",
    # },
    # "broker_goto": {
    #     "name": "BROKERAPP - GO 2 LOGISTICS",
    #     "base_url": "https://broker.goto-logistics.com",
    #     "login_path": "/login",
    #     "logs_path": "/logs",
    #     "username_env": "BROKER_GOTO_USER",
    #     "password_env": "BROKER_GOTO_PASS",
    # },
    # "klc_crossdock": {
    #     "name": "CROSSDOCK - KLC",
    #     "base_url": "https://klccrossdock.t4app.com",
    #     "login_path": "/login",
    #     "logs_path": "/logs",
    #     "username_env": "KLC_CD_USER",
    #     "password_env": "KLC_CD_PASSWORD",
    # },
    # "t4tms_backend": {
    #     "name": "T4TMS - BACKEND",
    #     "base_url": "https://backend.t4tms.us",
    #     "login_path": "/logs",  # T4TMS uses HTTP Basic Auth directly on /logs
    #     "logs_path": "/logs",
    #     "username_env": "T4TMS_BACKEND_USER",
    #     "password_env": "T4TMS_BACKEND_PASSWORD",
    # },
}


def get_apps_config_from_db() -> Dict[str, Dict]:
    """
    Load active apps from database.
    Returns empty dict if database is unavailable or no apps found.
    """
    try:
        from t4alerts_backend.apps_manager.models import MonitoredApp
        return MonitoredApp.to_config_format()
    except Exception as e:
        print(f"  ⚠️ Warning: Could not load apps from database: {e}")
        return {}


def get_apps_config() -> Dict[str, Dict]:
    """
    Get app configuration with hybrid approach:
    1. Try to load from database
    2. If database has apps, merge with legacy config (DB takes precedence)
    3. If database is empty or unavailable, use legacy hardcoded config
    
    This ensures backward compatibility while enabling dynamic configuration.
    """
    # Try database first
    db_config = get_apps_config_from_db()
    
    if db_config:
        # Database has apps - convert legacy format to match DB format
        legacy_converted = {}
        for app_key, config in APPS_CONFIG_LEGACY.items():
            # Skip if already in database
            if app_key in db_config:
                continue
            
            # Convert legacy format (env vars) to direct credentials
            username = os.getenv(config.get("username_env", ""))
            password = os.getenv(config.get("password_env", ""))
            
            if username and password:
                legacy_converted[app_key] = {
                    "name": config["name"],
                    "base_url": config["base_url"],
                    "login_path": config["login_path"],
                    "logs_path": config["logs_path"],
                    "username": username,
                    "password": password,
                }
        
        # Merge: DB apps + legacy apps not in DB
        merged = {**legacy_converted, **db_config}
        print(f"  ✅ Loaded {len(db_config)} apps from database, {len(legacy_converted)} from legacy config")
        return merged
    
    # Fallback: use legacy config with env vars
    print(f"  ℹ️ Using legacy hardcoded config ({len(APPS_CONFIG_LEGACY)} apps)")
    return APPS_CONFIG_LEGACY


# Dynamic config - Initialize with legacy defaults safely
# We avoid calling get_apps_config() at module level to prevent "working outside context" errors
APPS_CONFIG = APPS_CONFIG_LEGACY.copy()


def get_app_credentials(app_key: str) -> tuple[str, str, str]:
    """
    Obtiene las credenciales y nombre de una aplicación.
    Soporta formato legacy y carga dinámica de BD.
    
    Args:
        app_key: clave en APPS_CONFIG (ej: 'driverapp_goto')
    
    Returns:
        (app_name, username, password)
    
    Raises:
        RuntimeError: si faltan credenciales
    """
    # Try global lookup first
    config = APPS_CONFIG.get(app_key)
    
    # If not found, try to load from DB dynamically (Context must be active)
    if not config:
        try:
            current_config = get_apps_config()
            config = current_config.get(app_key)
        except Exception as e:
            print(f"⚠️ Warning: Failed to reload config dynamically: {e}")

    if not config:
        raise ValueError(f"Aplicación '{app_key}' no encontrada en APPS_CONFIG ni DB")
    
    app_name = config["name"]
    
    # New format: credentials stored directly
    if "username" in config and "password" in config:
        username = config["username"]
        password = config["password"]
    # Legacy format: credentials from env vars
    elif "username_env" in config and "password_env" in config:
        username = os.getenv(config["username_env"])
        password = os.getenv(config["password_env"])
    else:
        raise RuntimeError(
            f"Configuración inválida para {app_name}. "
            f"Falta 'username'/'password' o 'username_env'/'password_env'"
        )
    
    if not username or not password:
        raise RuntimeError(
            f"Faltan credenciales para {app_name}. "
            f"Verifica la configuración o variables de entorno"
        )
    
    return app_name, username, password


def get_app_urls(app_key: str) -> tuple[str, str, str]:
    """
    Obtiene las URLs de una aplicación.
    Soporta carga dinámica desde BD.
    
    Args:
        app_key: clave en APPS_CONFIG
    
    Returns:
        (base_url, login_url, logs_url)
    """
    config = APPS_CONFIG.get(app_key)
    
    # Fallback to dynamic load if not in global config
    if not config:
        try:
            current_config = get_apps_config()
            config = current_config.get(app_key)
        except Exception as e:
            print(f"⚠️ Warning: Failed to reload config dynamically in get_app_urls: {e}")

    if not config:
        raise ValueError(f"Aplicación '{app_key}' no encontrada en APPS_CONFIG ni DB")
    
    base_url = config["base_url"]
    login_path = config.get("login_path", "/login") 
    logs_path = config.get("logs_path", "/logs")
    
    # Handle cases where paths might already be full URLs (legacy flexibility)
    if "://" in login_path:
        login_url = login_path
    else:
        login_url = base_url.rstrip('/') + '/' + login_path.lstrip('/')
        
    if "://" in logs_path:
        logs_url = logs_path
    else:
        logs_url = base_url.rstrip('/') + '/' + logs_path.lstrip('/')
    
    return base_url, login_url, logs_url


def get_sms_app_name(app_key: str) -> str:
    """
    Obtiene el nombre específico de la aplicación para mensajes SMS.
    """
    # Try dynamic load if needed
    name = SMS_APP_NAMES.get(app_key)
    if name:
        return name
        
    config = APPS_CONFIG.get(app_key)
    if not config:
        try:
            current_config = get_apps_config()
            config = current_config.get(app_key)
        except:
            pass
            
    if config:
        return config.get("name", app_key)
        
    return app_key


# === RETROCOMPATIBILIDAD (para código existente) ===
# Si algo todavía usa estas variables, las asignamos desde la config de GoTo
USERNAME = os.getenv("DRIVERAPP_USER")
PASSWORD = os.getenv("DRIVERAPP_PASS")

if not USERNAME or not PASSWORD:
    raise RuntimeError("Faltan DRIVERAPP_USER o DRIVERAPP_PASS en el archivo .env")