# app/logs_scraper.py
from bs4 import BeautifulSoup

from .config import KEYWORDS_NO_CONTROLADO, get_app_urls


def fetch_logs_html(session, fecha_str: str, app_key: str = "driverapp_goto") -> str:
    """
    Obtiene el HTML de los logs para una fecha dada de una aplicación específica.
    
    Args:
        session: sesión autenticada (requests.Session)
        fecha_str: fecha en formato "YYYY-MM-DD"
        app_key: clave de la aplicación en APPS_CONFIG
    
    Returns:
        HTML de la página de logs
    """
    _, _, logs_url = get_app_urls(app_key)
    
    params = {
        "date": fecha_str,
    }
    resp = session.get(logs_url, params=params)
    resp.raise_for_status()
    return resp.text


def _es_no_controlado(texto: str) -> bool:
    """
    Devuelve True si el texto parece un error no controlado
    según las palabras clave definidas en KEYWORDS_NO_CONTROLADO.
    """
    t = texto.lower()
    return any(keyword in t for keyword in KEYWORDS_NO_CONTROLADO)


def _resumir_mensaje(texto: str) -> str:
    """
    Corta el mensaje a algo más legible:

    - Si encuentra '[stacktrace]', se queda solo con lo que hay antes.
    - Si encuentra info del Request/headers ({"Request...", Accept:, Host:, etc.),
      también corta antes de eso.

    Esto es solo para MOSTRAR el mensaje; para clasificar
    seguimos usando el texto completo.
    """
    marcadores_corte = [
        "[stacktrace]",
        '{"Request',       # donde empieza el log del Request
        '"Request : "',    # variante posible
        "Accept:",
        "Host:",
        "User-Agent:",
        "X-Requested-With:",
    ]

    pos_corte = len(texto)
    for marcador in marcadores_corte:
        p = texto.find(marcador)
        if p != -1 and p < pos_corte:
            pos_corte = p

    texto = texto[:pos_corte].strip()
    return texto


def classify_logs(html: str):
    """
    Parsea el HTML, se queda con Level = error,
    y los separa en controlados / no controlados.

    Devuelve (errores_controlados, errores_no_controlados) como listas de strings,
    donde cada string tiene el formato:
        ERROR - production - 2025-11-26 14:30:44 - Mensaje resumido
    """
    soup = BeautifulSoup(html, "html.parser")

    # AJUSTA este selector a tu HTML real si hace falta
    rows = soup.select("table tbody tr")

    errores_controlados = []
    errores_no_controlados = []

    # Contadores para comparar con lo que muestra la página
    total_registros = 0       # todos los registros de la tabla (cualquier Level)
    total_errors = 0          # solo registros con Level = error

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]

        # Necesitamos al menos: Level, Context/Environment, Fecha, Mensaje
        if len(cols) < 4:
            continue

        total_registros += 1

        # Si la tabla tiene más de 4 columnas, nos quedamos con las primeras 4
        level, context, fecha, content = cols[:4]

        # Solo nos interesan los que tienen Level = error
        if level.lower() != "error":
            continue

        total_errors += 1

        # Usamos el contenido COMPLETO para clasificar...
        if _es_no_controlado(content):
            tipo_lista = errores_no_controlados
        else:
            tipo_lista = errores_controlados

        # ...pero mostramos una versión resumida
        mensaje_resumido = _resumir_mensaje(content)

        # Formato que querías:
        # ERROR - production - 2025-11-26 14:04:48 - Mensaje resumido
        log_line = f"{level.upper()} - {context} - {fecha} - {mensaje_resumido}"
        tipo_lista.append(log_line)

    return errores_controlados, errores_no_controlados
