# app/session_manager.py
import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, LOGIN_PATH, USERNAME, PASSWORD


def create_logged_session() -> requests.Session:
    session = requests.Session()
    login_url = BASE_URL + LOGIN_PATH  # suele ser "https://driverapp.goto-logistics.com/login"

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
        "identity": USERNAME,
        "password": PASSWORD,
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
        raise RuntimeError("❌ Login falló: revisa USERNAME/PASSWORD o el payload del formulario")

    # (Opcional) probar acceder directo a /logs
    # logs_url = BASE_URL + LOGS_PATH
    # test = session.get(logs_url)
    # print("Después del login, GET /logs ->", test.url)

    return session
