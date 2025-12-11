# app/logs_scraper.py
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from app.config import KEYWORDS_NO_CONTROLADO, get_app_urls

def fetch_logs_html(session, fecha_str: str, app_key: str = "driverapp_goto") -> str:
    """
    Obtiene el HTML de los logs para una fecha dada de una aplicación específica.

    Hace dos pasos:
    1) GET /logs -> lista de archivos (laravel-YYYY-MM-DD.log y sus ?l=...)
    2) Busca el enlace correspondiente a la fecha pedida y hace GET a ese ?l=...
    """
    # 1) Obtenemos la URL base de logs para esa app
    _, _, logs_url = get_app_urls(app_key)

    # 2) Cargamos la página principal de logs (lista de archivos)
    resp_index = session.get(logs_url, timeout=30)
    resp_index.raise_for_status()
    index_html = resp_index.text

    soup = BeautifulSoup(index_html, "html.parser")

    # Nombre del archivo estándar
    target_date_suffix = f"-{fecha_str}.log"
    strict_target = f"laravel-{fecha_str}.log"

    link_tag = None
    available_files = []
    
    # Recorremos todos los links para buscar match
    for a in soup.select("div.list-group a"):
        text = (a.get_text() or "").strip()
        available_files.append(text)
        
        # 1. Prioridad: Coincidencia exacta
        if text == strict_target:
            link_tag = a
            break
        
        # 2. Fallback: Coincidencia parcial por fecha (ej: worker-2025-12-11.log)
        # Solo si no hemos encontrado uno estricto aún
        if link_tag is None and text.endswith(target_date_suffix):
            link_tag = a
            # No hacemos break inmediato por si luego aparece el estricto, 
            # pero en este loop simple, si aparece el estricto después, lo sobrescribiría?
            # Mejor: Si encontramos el estricto, break. Si encontramos parcial, guardamos y seguimos.
            # Pero para simplificar: si encontramos strict -> break.
            
    # Si después del loop tenemos un link_tag (ya sea estricto o parcial), lo usamos.
    
    if link_tag is None:
        # Debug info: imprimir qué archivos había
        msg = (
            f"No se encontró log para {fecha_str} en {app_key}. "
            f"Buscado: *{target_date_suffix}. "
            f"Archivos disponibles: {available_files}"
        )
        raise RuntimeError(msg)

    # href viene en formato "?l=eyJpdiI6..."
    href = link_tag.get("href") or ""
    logs_day_url = urljoin(logs_url, href)

    # 3) Cargamos ahora SÍ el log correspondiente a esa fecha
    resp_day = session.get(logs_day_url, timeout=30)
    resp_day.raise_for_status()
    logs_html = resp_day.text

    # # DEBUG - Guardamos para depurar, como ya hacías
    # debug_path = Path(f"debug_logs_{app_key}.html")
    # debug_path.write_text(logs_html, encoding="utf-8")

    return logs_html

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

        # Formato completo sin resumir:
        # ERROR - production - 2025-11-26 14:04:48 - Mensaje completo
        log_line = f"{level.upper()} - {context} - {fecha} - {content}"
        tipo_lista.append(log_line)

    return errores_controlados, errores_no_controlados
