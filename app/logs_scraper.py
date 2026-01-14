# app/logs_scraper.py
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

from app.config import KEYWORDS_NO_CONTROLADO, get_app_urls


class StaleLogsError(Exception):
    """Exception raised when log files haven't been updated for 2+ days."""
    def __init__(self, message, app_key, fecha_str, days_old, most_recent_date):
        super().__init__(message)
        self.app_key = app_key
        self.fecha_str = fecha_str
        self.days_old = days_old
        self.most_recent_date = most_recent_date

def fetch_logs_html(session, fecha_str: str, app_key: str = "driverapp_goto") -> str:
    """
    Obtiene el HTML de los logs para una fecha dada de una aplicación específica.
    
    Si no encuentra logs para la fecha solicitada:
    - Si es fecha FUTURA: lanza error sin fallback (no tiene sentido buscar logs que no existen)
    - Si es fecha HOY o PASADA: intenta con el día anterior (útil para ejecuciones a medianoche)

    Hace dos pasos:
    1) GET /logs -> lista de archivos (laravel-YYYY-MM-DD.log y sus ?l=...)
    2) Busca el enlace correspondiente a la fecha pedida y hace GET a ese ?l=...
    
    NOTE: T4App Admin uses JSON API, handled separately.
    """
    # Special handling for T4App which uses JSON API
    if app_key == "t4app_admin":
        return _fetch_logs_from_json_api(session, fecha_str, app_key)
    
    # 1) Obtenemos la URL base de logs para esa app
    _, _, logs_url = get_app_urls(app_key)

    # 2) Cargamos la página principal de logs (lista de archivos)
    resp_index = session.get(logs_url, timeout=60)
    resp_index.raise_for_status()
    index_html = resp_index.text

    soup = BeautifulSoup(index_html, "html.parser")

    # Intentar con la fecha original primero
    link_tag, fecha_usada = _buscar_log_por_fecha(soup, fecha_str)
    
    # Si no se encontró, verificar si debemos intentar con el día anterior
    if link_tag is None:
        # Obtener fecha actual (sin hora para comparar solo fechas)
        fecha_hoy = datetime.now().date()
        fecha_solicitada_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        
        # ¿Es fecha futura?
        if fecha_solicitada_obj > fecha_hoy:
            # NO usar fallback para fechas futuras
            available_files = [a.get_text(strip=True) for a in soup.select("div.list-group a")]
            msg = (
                f"⚠️ No se puede procesar fecha futura {fecha_str} en {app_key}. "
                f"La fecha solicitada es posterior a hoy ({fecha_hoy}). "
                f"Los logs aún no existen. "
                f"Archivos disponibles: {available_files}"
            )
            raise RuntimeError(msg)
        
        # Si es fecha HOY o PASADA, intentar con el día anterior
        fecha_anterior_obj = fecha_solicitada_obj - timedelta(days=1)
        fecha_anterior_str = fecha_anterior_obj.strftime("%Y-%m-%d")
        
        print(f"   ⚠️ No se encontró log para {fecha_str}, intentando con {fecha_anterior_str}...")
        
        link_tag, fecha_usada = _buscar_log_por_fecha(soup, fecha_anterior_str)
        
        if link_tag is not None:
            print(f"   ✓ Usando logs del día anterior ({fecha_anterior_str})")
    
    # Si después de intentar ambas fechas no hay resultados
    if link_tag is None:
        available_files = [a.get_text(strip=True) for a in soup.select("div.list-group a")]
        
        # Verificar si los logs están desactualizados (2+ días)
        most_recent_date, days_old = _get_most_recent_log_date(soup)
        
        if most_recent_date and days_old >= 2:
            # Los logs están desactualizados por 2 o más días
            msg = (
                f"WARNING: Log files have not been created for two or more days in {app_key}. "
                f"Most recent log: {most_recent_date} ({days_old} days old). "
                f"Requested: {fecha_str}. Available files: {available_files}"
            )
            raise StaleLogsError(msg, app_key, fecha_str, days_old, most_recent_date)
        else:
            # Error normal - logs no encontrados pero están relativamente actuales
            msg = (
                f"No se encontró log para {fecha_str} ni para el día anterior en {app_key}. "
                f"Archivos disponibles: {available_files}"
            )
            raise RuntimeError(msg)

    # href viene en formato "?l=eyJpdiI6..."
    href = link_tag.get("href") or ""
    logs_day_url = urljoin(logs_url, href)

    # 3) Cargamos ahora SÍ el log correspondiente a esa fecha
    resp_day = session.get(logs_day_url, timeout=60)
    resp_day.raise_for_status()
    logs_html = resp_day.text

    # # DEBUG - Guardamos para depurar, como ya hacías
    # debug_path = Path(f"debug_logs_{app_key}.html")
    # debug_path.write_text(logs_html, encoding="utf-8")

    return logs_html


def _fetch_logs_from_json_api(session, fecha_str: str, app_key: str) -> str:
    """
    Fetches logs from T4App Admin's API.
    
    T4App requires requesting HTML (not JSON) to get encrypted token links.
    Each log file has a link like ?l=<encrypted_token> that must be followed.
    """
    from urllib.parse import urljoin
    _, _, logs_url = get_app_urls(app_key)
    
    # Step 1: Get list of available log files as HTML (NOT JSON)
    # We need to request HTML to get the encrypted token links
    headers_html = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    resp_index = session.get(logs_url, headers=headers_html, timeout=60)
    resp_index.raise_for_status()
    
    # Parse HTML to find log file links
    soup = BeautifulSoup(resp_index.text, "html.parser")
    
    # Step 2: Find the log file link for the requested date
    target_filename = f"laravel-{fecha_str}.log"
    
    # Search for the link with the target filename
    link_tag = None
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        if text == target_filename:
            link_tag = a
            break
    
    if link_tag is None:
        # Try previous day as fallback
        fecha_hoy = datetime.now().date()
        fecha_solicitada_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        
        if fecha_solicitada_obj > fecha_hoy:
            available_files = [a.get_text(strip=True) for a in soup.find_all('a', href=True) if '.log' in a.get_text()]
            msg = (
                f"⚠️ No se puede procesar fecha futura {fecha_str} en {app_key}. "
                f"Archivos disponibles: {available_files}"
            )
            raise RuntimeError(msg)
        
        fecha_anterior_obj = fecha_solicitada_obj - timedelta(days=1)
        fecha_anterior_str = fecha_anterior_obj.strftime("%Y-%m-%d")
        target_filename_anterior = f"laravel-{fecha_anterior_str}.log"
        
        print(f"   ⚠️ No se encontró log para {fecha_str}, intentando con {fecha_anterior_str}...")
        
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            if text == target_filename_anterior:
                link_tag = a
                target_filename = target_filename_anterior
                print(f"   ✓ Usando logs del día anterior ({fecha_anterior_str})")
                break
        
        if link_tag is None:
            # Check for stale logs
            date_pattern = re.compile(r'laravel-(\d{4}-\d{2}-\d{2})\.log')
            log_dates = []
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                match = date_pattern.match(text)
                if match:
                    try:
                        log_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                        log_dates.append(log_date)
                    except ValueError:
                        continue
            
            if log_dates:
                most_recent = max(log_dates)
                today = datetime.now().date()
                days_old = (today - most_recent).days
                
                if days_old >= 2:
                    available_files = [a.get_text(strip=True) for a in soup.find_all('a', href=True) if '.log' in a.get_text()]
                    msg = (
                        f"WARNING: Log files have not been created for two or more days in {app_key}. "
                        f"Most recent log: {most_recent} ({days_old} days old). "
                        f"Requested: {fecha_str}. Available files: {available_files}"
                    )
                    raise StaleLogsError(msg, app_key, fecha_str, days_old, most_recent)
            
            available_files = [a.get_text(strip=True) for a in soup.find_all('a', href=True) if '.log' in a.get_text()]
            raise RuntimeError(f"No se encontró log para {fecha_str} ni para el día anterior en {app_key}. Archivos: {available_files}")
    
    # Step 3: Get the encrypted token from the link href
    # href format: ?l=eyJpdiI6I...
    href = link_tag.get('href') or ''
    if not href.startswith('?l='):
        raise RuntimeError(f"T4App Admin link format unexpected for {target_filename}: {href}")
    
    # Build full URL with the encrypted token
    log_file_url = urljoin(logs_url, href)
    
    # Step 4: Fetch the specific log file content using the encrypted token
    resp_content = session.get(log_file_url, headers=headers_html, timeout=60)
    resp_content.raise_for_status()
    
    # Return the HTML (it returns rendered HTML table with log entries)
    return resp_content.text


def _get_most_recent_log_date(soup: BeautifulSoup) -> tuple:
    """
    Extrae las fechas de todos los archivos de log disponibles y devuelve la más reciente.
    
    Returns:
        tuple: (most_recent_date, days_old) donde most_recent_date es un objeto date
               y days_old es el número de días desde hoy hasta esa fecha (positivo = pasado)
               Devuelve (None, None) si no se encuentran archivos de log con fechas válidas.
    """
    # Pattern para extraer fechas YYYY-MM-DD de nombres de archivo
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})\.log')
    
    log_dates = []
    for a in soup.select("div.list-group a"):
        text = (a.get_text() or "").strip()
        match = date_pattern.search(text)
        if match:
            try:
                log_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                log_dates.append(log_date)
            except ValueError:
                continue
    
    if not log_dates:
        return None, None
    
    most_recent = max(log_dates)
    today = datetime.now().date()
    days_old = (today - most_recent).days
    
    return most_recent, days_old


def _buscar_log_por_fecha(soup: BeautifulSoup, fecha_str: str) -> tuple:
    """
    Busca un archivo de log para una fecha específica en el HTML parseado.
    
    Returns:
        tuple: (link_tag, fecha_usada) donde link_tag es el elemento <a> encontrado 
               (o None si no se encuentra), y fecha_usada es la fecha del log encontrado
    """
    # Nombre del archivo estándar
    target_date_suffix = f"-{fecha_str}.log"
    strict_target = f"laravel-{fecha_str}.log"

    link_tag = None
    
    # Recorremos todos los links para buscar match
    for a in soup.select("div.list-group a"):
        text = (a.get_text() or "").strip()
        
        # 1. Prioridad: Coincidencia exacta
        if text == strict_target:
            link_tag = a
            break
        
        # 2. Fallback: Coincidencia parcial por fecha (ej: worker-2025-12-11.log)
        # Solo si no hemos encontrado uno estricto aún
        if link_tag is None and text.endswith(target_date_suffix):
            link_tag = a
            
    return link_tag, fecha_str

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
