# app/session_manager.py
"""
AppSession — Context manager que provee una requests.Session autenticada.

Encapsula las tres estrategias de autenticación:
  - Formulario HTML (GoTo, KLC, GoExperior, …)
  - JWT API (T4App Admin)
  - HTTP Basic Auth (T4TMS Backend)

Uso:
    with AppSession(app_key) as session:
        html = session.get(url).text

Compatibilidad hacia atrás:
    create_logged_session() sigue existiendo como alias de fábrica.
"""
from __future__ import annotations

import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

from .config import get_app_credentials, get_app_urls


class AppSession:
    """
    Context manager que devuelve una requests.Session autenticada.

    Auth strategy se selecciona automáticamente del campo 'auth_type' en
    APPS_CONFIG, o por heurística basada en app_key.
    """

    def __init__(self, app_key: str, max_retries: int = 3, timeout: int = None):
        self.app_key = app_key
        self.max_retries = max_retries
        self.timeout = timeout
        self._session: requests.Session | None = None

    # ------------------------------------------------ context manager API ---

    def __enter__(self) -> requests.Session:
        self._session = self._authenticate()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    # ---------------------------------------------------- authentication ---

    def _authenticate(self) -> requests.Session:
        """Elige la estrategia de autenticación según config."""
        from .config import APPS_CONFIG
        config = APPS_CONFIG.get(self.app_key, {})
        auth_type = config.get("auth_type")

        if auth_type == "jwt_api":
            return self._login_jwt()
        elif self.app_key == "t4tms_backend":
            return self._login_basic()
        else:
            return self._login_form()

    def _make_session(self) -> requests.Session:
        """Crea una Session con retry automático en errores HTTP transitorios."""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _retry_delays(self) -> list[int]:
        return [5, 10, 20]

    # ------------------------------------------ authentication strategies --

    def _login_form(self) -> requests.Session:
        """Autenticación por formulario HTML (CSRF token + POST)."""
        app_name, username, password = get_app_credentials(self.app_key)
        base_url, login_url, logs_url = get_app_urls(self.app_key)
        TIMEOUT = (10, self.timeout or 60)

        print(f"🔐 Autenticando en {app_name} ({base_url}) con formulario de login...")

        last_exc = None
        for attempt in range(self.max_retries):
            try:
                session = self._make_session()

                # 1) GET login para CSRF
                resp = session.get(login_url, timeout=TIMEOUT)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                token_input = soup.find("input", {"name": "_token"})
                csrf_token = token_input["value"] if token_input else ""
                meta_csrf = soup.find("meta", {"name": "csrf-token"})
                meta_csrf_token = meta_csrf["content"] if meta_csrf else ""

                # Detectar campo de usuario dinámicamente
                field_name = "identity"
                for candidate in ("email", "identity", "username"):
                    if soup.find("input", {"name": candidate}):
                        field_name = candidate
                        break

                payload = {field_name: username, "password": password}
                if csrf_token:
                    payload["_token"] = csrf_token

                headers = {"Referer": login_url, "User-Agent": _UA}
                if meta_csrf_token:
                    headers["X-CSRF-TOKEN"] = meta_csrf_token

                # 2) POST login
                resp = session.post(login_url, data=payload, headers=headers,
                                    allow_redirects=True, timeout=TIMEOUT)
                resp.raise_for_status()

                # 3) Verificar éxito (si seguimos en /login → falló)
                if soup.find("input", {"name": "password"}) and 'name="password"' in resp.text:
                    if "/login" in getattr(session, "url", "") or "login" in str(resp.url).split("/")[-1]:
                        raise RuntimeError(
                            f"❌ Login falló en {app_name}: revisa credenciales. Campo: {field_name}"
                        )

                print(f"✅ Autenticación exitosa en {app_name}")
                return session

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    wait = self._retry_delays()[attempt]
                    print(f"   ⚠️ Intento {attempt + 1}/{self.max_retries} falló: {type(e).__name__}")
                    print(f"   ⏳ Reintentando en {wait}s...")
                    time.sleep(wait)
                else:
                    raise requests.exceptions.ConnectionError(
                        f"❌ Error de conexión en {app_name} tras {self.max_retries} intentos: {e}"
                    ) from e

        raise requests.exceptions.ConnectionError(
            f"No se pudo conectar a {app_name}"
        ) from last_exc

    def _login_jwt(self) -> requests.Session:
        """Autenticación JWT API (T4App Admin)."""
        app_name, username, password = get_app_credentials(self.app_key)
        base_url, login_url, logs_url = get_app_urls(self.app_key)
        TIMEOUT = (10, self.timeout or 30)

        print(f"🔐 Autenticando en {app_name} ({base_url}) con JWT API...")

        session = self._make_session()
        last_exc = None

        for attempt in range(self.max_retries):
            try:
                headers = {
                    "User-Agent": _UA,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                resp = session.post(
                    login_url,
                    json={"email": username, "password": password},
                    headers=headers,
                    timeout=TIMEOUT,
                )
                if resp.status_code == 401:
                    raise RuntimeError(f"❌ Autenticación falló en {app_name}: credenciales inválidas")
                resp.raise_for_status()

                data = resp.json()
                if not data.get("status") or "token" not in data:
                    raise RuntimeError(f"❌ Respuesta de login inválida en {app_name}")

                access_token = data["token"]["accessToken"]
                session.headers.update({
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "User-Agent": _UA,
                })
                print(f"✅ Autenticación exitosa en {app_name}")
                return session

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    wait = self._retry_delays()[attempt]
                    print(f"   ⚠️ Intento {attempt + 1}/{self.max_retries} falló: {type(e).__name__}")
                    print(f"   ⏳ Reintentando en {wait}s...")
                    time.sleep(wait)
                else:
                    raise requests.exceptions.ConnectionError(
                        f"❌ Error de conexión en {app_name} tras {self.max_retries} intentos: {e}"
                    ) from e

        raise requests.exceptions.ConnectionError(
            f"No se pudo conectar a {app_name}"
        ) from last_exc

    def _login_basic(self) -> requests.Session:
        """Autenticación HTTP Basic Auth (T4TMS Backend)."""
        app_name, username, password = get_app_credentials(self.app_key)
        base_url, _, logs_url = get_app_urls(self.app_key)
        TIMEOUT = (10, self.timeout or 60)

        print(f"🔐 Autenticando en {app_name} ({base_url}) con HTTP Basic Auth...")

        session = self._make_session()
        session.auth = HTTPBasicAuth(username, password)
        last_exc = None

        for attempt in range(self.max_retries):
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
                last_exc = e
                if attempt < self.max_retries - 1:
                    wait = self._retry_delays()[attempt]
                    print(f"   ⚠️ Intento {attempt + 1}/{self.max_retries} falló: {type(e).__name__}")
                    print(f"   ⏳ Reintentando en {wait}s...")
                    time.sleep(wait)
                else:
                    raise requests.exceptions.ConnectionError(
                        f"❌ Error de conexión en {app_name} tras {self.max_retries} intentos: {e}"
                    ) from e

        raise requests.exceptions.ConnectionError(
            f"No se pudo conectar a {app_name}"
        ) from last_exc


# ------------------------------------------------------------ constants -----
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


# ------------------------------------------------- backward-compat alias ----

def create_logged_session(
    app_key: str = "driverapp_goto",
    max_retries: int = 3,
    timeout: int = None,
) -> AppSession:
    """
    Alias de fábrica para backward-compatibility.
    Devuelve un AppSession listo para usar como context manager:

        with create_logged_session(app_key) as session:
            html = session.get(url).text
    """
    return AppSession(app_key, max_retries=max_retries, timeout=timeout)
