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

# LEGACY: Hardcoded configuration (used for main.py automated tasks)
APPS_CONFIG_LEGACY: Dict[str, Dict] = {
    "driverapp_goto": {
        "name": "DRIVERAPP - GO 2 LOGISTICS",
        "base_url": "https://driverapp.goto-logistics.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "DRIVERAPP_USER",
        "password_env": "DRIVERAPP_PASS",
    },
    "goexperior": {
        "name": "DRIVERAPP - GOEXPERIOR",
        "base_url": "https://driverapp.goexperior.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "GOEXPERIOR_USER",
        "password_env": "GOEXPERIOR_PASS",
    },
    "klc": {
        "name": "T4APP - KLC",
        "base_url": "https://klc.t4app.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "KLC_USER",
        "password_env": "KLC_PASS",
    },
    "accuratecargo": {
        "name": "T4APP - ACCURATECARGO",
        "base_url": "https://accuratecargo.t4app.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "ACCURATECARGO_USER",
        "password_env": "ACCURATECARGO_PASS",
    },
    "broker_goto": {
        "name": "BROKERAPP - GO 2 LOGISTICS",
        "base_url": "https://broker.goto-logistics.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "BROKER_GOTO_USER",
        "password_env": "BROKER_GOTO_PASS",
    },
    "klc_crossdock": {
        "name": "CROSSDOCK - KLC",
        "base_url": "https://klccrossdock.t4app.com",
        "login_path": "/login",
        "logs_path": "/logs",
        "username_env": "KLC_CD_USER",
        "password_env": "KLC_CD_PASSWORD",
    },
    "t4tms_backend": {
        "name": "T4TMS - BACKEND",
        "base_url": "https://backend.t4tms.us",
        "login_path": "/logs",  # T4TMS uses HTTP Basic Auth directly on /logs
        "logs_path": "/logs",
        "username_env": "T4TMS_BACKEND_USER",
        "password_env": "T4TMS_BACKEND_PASSWORD",
    },
}

# Specific mapping for SMS notifications (prevent NameError)
SMS_APP_NAMES = {
    "driverapp_goto": "GOTO LOGISTICS",
    "goexperior": "GOEXPERIOR",
    "klc": "KLC",
    "accuratecargo": "ACCURATE",
    "broker_goto": "BROKER GOTO",
    "klc_crossdock": "CROSSDOCK KLC",
    "t4tms_backend": "T4TMS BACKEND"
}


# Caching for dynamic configurations
_DYNAMIC_CACHE: Dict[str, Dict] = {}
_LAST_CACHE_TIME = 0
CACHE_TTL = 30  # seconds


def get_apps_config_from_db() -> Dict[str, Dict]:
    """
    Load active apps from database.
    Returns empty dict if database is unavailable or no apps found.
    """
    try:
        from t4alerts_backend.apps_manager.models import MonitoredApp
        # Import moved to subfolder, we need to adjust sys.path or use relative
        # But here we are in app/config.py, root of project.
        # After restructuring, t4alerts_backend is in t4alerts_web/backend.
        # We might need to adjust imports.
        return MonitoredApp.to_config_format()
    except Exception as e:
        # Silently fail if DB not found or model not accessible (e.g. main.py outside context)
        return {}


def get_apps_config(dynamic_only: bool = False, quiet: bool = False) -> Dict[str, Dict]:
    """
    Get app configuration with modular approach:
    - dynamic_only=True (Web): Returns ONLY apps from DB (saved via Custom Scan)
    - dynamic_only=False (Automation): Returns legacy static apps + DB apps
    """
    global _DYNAMIC_CACHE, _LAST_CACHE_TIME
    import time
    
    now = time.time()
    
    # 1. Use cache if valid (small TTL to allow nearly real-time updates)
    if _DYNAMIC_CACHE and (now - _LAST_CACHE_TIME < CACHE_TTL):
        return _DYNAMIC_CACHE if dynamic_only else {**_get_legacy_converted(), **_DYNAMIC_CACHE}

    # 2. Load from DB
    db_config = get_apps_config_from_db()
    _DYNAMIC_CACHE = db_config
    _LAST_CACHE_TIME = now
    
    # Update global reference for any direct access
    global APPS_CONFIG
    
    # 3. If Web mode (dynamic only), return DB apps (or empty if none)
    if dynamic_only:
        if db_config and not quiet:
            print(f"  ✅ Config: Loaded {len(db_config)} dynamic apps from database.")
        return db_config
    
    # 4. Automation mode (CLI/Main.py): Merge legacy + DB
    legacy_converted = _get_legacy_converted()
    merged = {**legacy_converted, **db_config}
    
    if not quiet:
        print(f"  ✅ Config: Loaded {len(merged)} total apps ({len(legacy_converted)} static, {len(db_config)} dynamic)")
    
    # Update global cache for performance
    APPS_CONFIG.update(merged)
    
    return merged


def _get_legacy_converted() -> Dict[str, Dict]:
    """Helper to convert legacy config using env vars."""
    legacy_converted = {}
    for app_key, config in APPS_CONFIG_LEGACY.items():
        # Resolve credentials from env
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
    return legacy_converted


# Global default (Start empty or with legacy depending on context)
# For CLI, we will call get_apps_config(dynamic_only=False) explicitly in main.py
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
            # Try to fetch from DB without being noisy
            current_config = get_apps_config(quiet=True)
            config = current_config.get(app_key)
            if config:
                # Cache it globally so we don't repeat this check
                APPS_CONFIG[app_key] = config
        except Exception:
            pass

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
            current_config = get_apps_config(quiet=True)
            config = current_config.get(app_key)
            if config:
                APPS_CONFIG[app_key] = config
        except Exception:
            pass

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