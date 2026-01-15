# app/session_manager.py
import requests
from bs4 import BeautifulSoup
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.auth import HTTPBasicAuth

from .config import get_app_credentials, get_app_urls


def create_logged_session(app_key: str = "driverapp_goto", max_retries: int = 3) -> requests.Session:
    """
    Crea una sesión autenticada para una aplicación específica con retry logic.
    
    T4TMS Backend uses HTTP Basic Auth directly on /logs endpoint.
    T4App Admin uses JWT API authentication.
    Other apps use traditional form-based login.
    
    Auth type is detected from config's 'auth_type' field or inferred from app_key.
    
    Args:
        app_key: clave de la aplicación en APPS_CONFIG (default: 'driverapp_goto')
        max_retries: número máximo de intentos de conexión (default: 3)
    
    Returns:
        requests.Session autenticada
    
    Raises:
        RuntimeError: si el login falla después de todos los reintentos
        requests.exceptions.ConnectionError: si no se puede establecer conexión
        requests.exceptions.Timeout: si la conexión excede el timeout
    """
    # Get config to check auth_type
    from .config import APPS_CONFIG
    config = APPS_CONFIG.get(app_key, {})
    auth_type = config.get('auth_type')
    
    # Determine authentication method
    # Priority: auth_type field > hardcoded app_key checks
    if auth_type == 'jwt_api':
        # JWT API authentication (T4App Admin and any ad-hoc T4App scans)
        return _create_jwt_api_session(app_key, max_retries)
    elif app_key == "t4tms_backend":
        # HTTP Basic Auth (T4TMS Backend)
        return _create_basic_auth_session(app_key, max_retries)
    else:
        # Traditional form-based login (most apps)
        return _create_form_login_session(app_key, max_retries)


def _create_basic_auth_session(app_key: str, max_retries: int = 3) -> requests.Session:
    """
    Creates a session with HTTP Basic Authentication for T4TMS backend.
    Authentication happens directly on the /logs endpoint.
    """
    app_name, username, password = get_app_credentials(app_key)
    base_url, _, logs_url = get_app_urls(app_key)
    
    print(f"🔐 Autenticando en {app_name} ({base_url}) con HTTP Basic Auth...")
    
    session = requests.Session()
    
    # Configure HTTP Basic Auth for all requests
    session.auth = HTTPBasicAuth(username, password)
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Test authentication by accessing /logs
    TIMEOUT = (10, 30)
    last_exception = None
    retry_delays = [5, 10, 20]
    
    for attempt in range(max_retries):
        try:
            resp = session.get(logs_url, timeout=TIMEOUT)
            
            if resp.status_code == 401:
                raise RuntimeError(f"❌ Autenticación falló en {app_name}: credenciales inválidas")
            
            resp.raise_for_status()
            print(f"✅ Autenticación exitosa en {app_name}")
            return session
            
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"   ⚠️ Intento {attempt + 1}/{max_retries} falló: {type(e).__name__}")
                print(f"   ⏳ Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                error_msg = f"❌ Error de conexión en {app_name} después de {max_retries} intentos: {str(e)}"
                print(f"   {error_msg}")
                raise requests.exceptions.ConnectionError(error_msg) from e
    
    raise requests.exceptions.ConnectionError(
        f"No se pudo conectar a {app_name} después de {max_retries} intentos"
    ) from last_exception


def _create_jwt_api_session(app_key: str, max_retries: int = 3) -> requests.Session:
    """
    Creates a session with JWT API authentication for T4App Admin.
    Authentication happens via POST to /api/login which returns a JWT token.
    """
    app_name, username, password = get_app_credentials(app_key)
    base_url, login_url, logs_url = get_app_urls(app_key)
    
    print(f"🔐 Autenticando en {app_name} ({base_url}) con JWT API...")
    
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Test authentication by logging in and getting JWT token
    TIMEOUT = (10, 30)
    last_exception = None
    retry_delays = [5, 10, 20]
    
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'email': username,
                'password': password
            }
            
            resp = session.post(login_url, json=payload, headers=headers, timeout=TIMEOUT)
            
            if resp.status_code == 401:
                raise RuntimeError(f"❌ Autenticación falló en {app_name}: credenciales inválidas")
            
            resp.raise_for_status()
            
            # Extract JWT token from response
            response_data = resp.json()
            if not response_data.get('status') or 'token' not in response_data:
                raise RuntimeError(f"❌ Respuesta de login inválida en {app_name}")
            
            access_token = response_data['token']['accessToken']
            
            # Store token in session headers for future requests
            session.headers.update({
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            
            print(f"✅ Autenticación exitosa en {app_name}")
            return session
            
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"   ⚠️ Intento {attempt + 1}/{max_retries} falló: {type(e).__name__}")
                print(f"   ⏳ Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                error_msg = f"❌ Error de conexión en {app_name} después de {max_retries} intentos: {str(e)}"
                print(f"   {error_msg}")
                raise requests.exceptions.ConnectionError(error_msg) from e
    
    raise requests.exceptions.ConnectionError(
        f"No se pudo conectar a {app_name} después de {max_retries} intentos"
    ) from last_exception


def _create_form_login_session(app_key: str, max_retries: int = 3) -> requests.Session:
    """
    Creates a session with traditional form-based login.
    Used for most applications (GoTo, GoExperior, KLC, etc.)
    """
    app_name, username, password = get_app_credentials(app_key)
    base_url, login_url, logs_url = get_app_urls(app_key)
    
    print(f"🔐 Autenticando en {app_name} ({base_url}) con formulario de login...")
    
    # Configuración de timeouts
    # (connect_timeout, read_timeout) en segundos
    TIMEOUT = (10, 60)
    
    # Configuración de retry con backoff exponencial
    retry_delays = [5, 10, 20]  # segundos entre intentos
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            
            # Configurar retry automático para HTTP adapter
            retry_strategy = Retry(
                total=2,  # reintentos automáticos por request
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 1) GET al login para obtener el token CSRF
            resp = session.get(login_url, timeout=TIMEOUT)
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

            # print(f"   ℹ️ Campo detectado para login: {field_name}")

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
            resp = session.post(login_url, data=payload, headers=headers, allow_redirects=True, timeout=TIMEOUT)
            resp.raise_for_status()

            # 3) Comprobación de éxito
            # Si seguimos viendo el form de login, es que falló
            # Buscamos el input de password o el token, eso indica que seguimos en login
            if soup.find("input", {"name": "password"}) and ('name="password"' in resp.text):
                 # Verificamos si seguimos en la página de login (redirección fallida)
                 if '/login' in session.url or 'login' in session.url.split('/')[-1]:
                     print(f"❌ Login falló. URL final: {session.url}")
                     print(f"   Usuario intentado: {username}")
                     raise RuntimeError(f"❌ Login falló en {app_name}: revisa credenciales o el payload. Campo usado: {field_name}. Usuario: {username}")

            print(f"✅ Autenticación exitosa en {app_name}")
            
            return session
            
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = retry_delays[attempt]
                print(f"   ⚠️ Intento {attempt + 1}/{max_retries} falló: {type(e).__name__}")
                print(f"   ⏳ Reintentando en {wait_time} segundos...")
                time.sleep(wait_time)
            else:
                error_msg = f"❌ Error de conexión en {app_name} después de {max_retries} intentos: {str(e)}"
                print(f"   {error_msg}")
                raise requests.exceptions.ConnectionError(error_msg) from e
    
    # Este punto solo se alcanza si todos los reintentos fallaron
    raise requests.exceptions.ConnectionError(
        f"No se pudo conectar a {app_name} después de {max_retries} intentos"
    ) from last_exception
