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

    # DETECCION DINAMICA DEL CAMPO DE LOGIN (identity vs email)
    # Algunos apps usan "identity", otros "email"
    field_name = "identity" # default fallback
    if soup.find("input", {"name": "email"}):
        field_name = "email"
    elif soup.find("input", {"name": "identity"}):
        field_name = "identity"
    elif soup.find("input", {"name": "username"}):
        field_name = "username"

    print(f"   ℹ️ Campo detectado para login: {field_name}")

    payload = {
        field_name: username,
        "password": password,
    }
    if csrf_token:
        payload["_token"] = csrf_token

    headers = {}
    if meta_csrf_token:
        headers["X-CSRF-TOKEN"] = meta_csrf_token
    headers["Referer"] = login_url
    headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

    # 2) POST de login
    resp = session.post(login_url, data=payload, headers=headers, allow_redirects=True)
    resp.raise_for_status()

    # 3) Comprobación de éxito
    # Si seguimos viendo el form de login, es que falló
    # Buscamos el input de password o el token, eso indica que seguimos en login
    if soup.find("input", {"name": "password"}) and ('name="password"' in resp.text):
         # Doble check: si el response url es el mismo que login url
         if resp.url.split('?')[0] == login_url.split('?')[0]:
             raise RuntimeError(f"❌ Login falló en {app_name}: revisa credenciales o el payload. Campo usado: {field_name}")

    print(f"✅ Autenticación exitosa en {app_name}")
    
    return session
