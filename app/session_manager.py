# app/session_manager.py
import requests
from bs4 import BeautifulSoup

from .config import get_app_credentials, get_app_urls


def create_logged_session(app_key: str = "driverapp_goto") -> requests.Session:
    """
    Crea una sesión autenticada para una aplicación específica.
    
    Args:
        app_key: clave de la aplicación en APPS_CONFIG (default: 'driverapp_goto')
    
    Returns:
        requests.Session autenticada
    
    Raises:
        RuntimeError: si el login falla
    """
    session = requests.Session()
    
    # Obtener credenciales y URLs
    app_name, username, password = get_app_credentials(app_key)
    base_url, login_url, logs_url = get_app_urls(app_key)
    
    print(f"🔐 Autenticando en {app_name} ({base_url})...")
    
    # 1) GET al login para obtener el token CSRF
    resp = session.get(login_url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # token del input hidden
    token_input = soup.find("input", {"name": "_token"})
    csrf_token = token_input["value"] if token_input else ""

    # también hay meta csrf, lo podemos usar en header
    meta_csrf = soup.find("meta", {"name": "csrf-token"})
    meta_csrf_token = meta_csrf["content"] if meta_csrf else ""

    # OJO: el campo se llama "identity"
    payload = {
        "identity": username,
        "password": password,
    }
    if csrf_token:
        payload["_token"] = csrf_token

    headers = {}
    if meta_csrf_token:
        headers["X-CSRF-TOKEN"] = meta_csrf_token
    headers["Referer"] = login_url

    # 2) POST de login
    resp = session.post(login_url, data=payload, headers=headers, allow_redirects=True)
    resp.raise_for_status()

    # 3) Comprobar rápido si seguimos en la página de login
    if 'id="validate"' in resp.text and "Welcome back to DriverApp!" in resp.text:
        raise RuntimeError(f"❌ Login falló en {app_name}: revisa credenciales o el payload del formulario")

    print(f"✅ Autenticación exitosa en {app_name}")
    
    return session
