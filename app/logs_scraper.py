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
    
    NOTE: T4App Admin uses JSON API/HTML tokens, handled separately via auth_type detection.
    """
    # Detect if this app uses JWT API (T4App Admin and ad-hoc scans)
    from app.config import APPS_CONFIG
    config = APPS_CONFIG.get(app_key, {})
    auth_type = config.get('auth_type', '')
    
    # Special handling for T4App which uses JSON API logic
    if app_key == "t4app_admin" or auth_type == "jwt_api":
        return _fetch_logs_from_json_api(session, fecha_str, app_key)
    
    # Special handling for T4TRANS which uses direct log file URLs
    if app_key == "t4trans" or auth_type == "t4trans_custom":
        return _fetch_logs_t4trans(session, fecha_str, app_key)
    
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
    
    # 4) Verificar si en lugar de la tabla hay un link de descarga (archivos grandes >50MB)
    soup_check = BeautifulSoup(logs_html, "html.parser")
    
    # Buscar link de descarga con patrón ?dl=
    download_link = soup_check.find('a', href=re.compile(r'\?dl='))
    
    if download_link:
        # Escenario de archivo grande - descargar y procesar
        logs_html = _download_and_process_large_log_file(session, logs_day_url, download_link, app_key)

    return logs_html


def _download_and_process_large_log_file(session, base_url: str, download_link, app_key: str = "unknown") -> str:
    """
    Descarga un archivo de log grande y lo convierte a formato HTML tabla.
    
    Cuando los archivos de log exceden ~50MB, Laravel log viewer muestra un link
    de descarga en vez de la tabla HTML. Esta función:
    1. Descarga el archivo usando streaming
    2. Parsea el contenido línea por línea
    3. Convierte a formato HTML tabla compatible con classify_logs()
    4. Limpia el archivo temporal
    
    Args:
        session: Sesión autenticada
        base_url: URL base para construir la URL de descarga
        download_link: Elemento <a> de BeautifulSoup con el href de descarga
        app_key: Identificador de la aplicación (para nombre de archivo temporal)
        
    Returns:
        str: HTML con tabla conteniendo los logs procesados
        
    Raises:
        requests.exceptions.RequestException: Si falla la descarga
    """
    import time
    
    # Extraer href del link de descarga (formato: ?dl=encrypted_token)
    href = download_link.get('href') or ''
    if not href:
        print("   ⚠️ Link de descarga sin href, retornando HTML vacío")
        return "<html><body><table><tbody></tbody></table></body></html>"
    
    # Construir URL completa de descarga
    download_url = urljoin(base_url, href)
    
    # Crear archivo temporal con nombre único
    temp_file = Path(f"/tmp/log_download_{app_key}_{int(time.time())}.log")
    
    try:
        print(f"   ⚠️ Archivo de logs grande detectado (>50MB), descargando...")
        
        # Descargar con streaming para no llenar memoria
        resp = session.get(download_url, stream=True, timeout=120)
        resp.raise_for_status()
        
        # Obtener tamaño del archivo si está disponible
        file_size = int(resp.headers.get('content-length', 0))
        file_size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
        
        # Escribir a archivo temporal en chunks
        with open(temp_file, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        actual_size_mb = temp_file.stat().st_size / (1024 * 1024)
        print(f"   ✓ Archivo descargado: {temp_file.name} ({actual_size_mb:.2f} MB)")
        
        # Parsear el archivo línea por línea
        html_rows = []
        error_count = 0
        
        # Patrón para capturar logs de Laravel:
        # [2026-02-15 10:55:43] production.ERROR: mensaje...
        log_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\w+)\.(\w+):\s+(.*?)(?=\n\[|\Z)',
            re.DOTALL
        )
        
        with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for match in log_pattern.finditer(content):
                timestamp = match.group(1)
                context = match.group(2)  # production, local, etc.
                level = match.group(3).upper()  # ERROR, DEBUG, INFO, etc.
                message = match.group(4).strip()
                
                # Limpiar mensaje de saltos de línea excesivos
                message = ' '.join(message.split())
                
                is_error = level == 'ERROR'
                is_info_with_error = level == 'INFO' and (
                    '"error":' in message.lower() or
                    '&quot;error&quot;:' in message.lower() or
                    '\\"error\\":' in message.lower()
                )
                
                # Solo procesar errores (e INFO con errors embebidos)
                if is_error or is_info_with_error:
                    error_count += 1
                    # Formato de fila HTML compatible con classify_logs()
                    row_html = f"""
                    <tr>
                        <td>error</td>
                        <td>{context}</td>
                        <td>{timestamp}</td>
                        <td>{message}</td>
                    </tr>
                    """
                    html_rows.append(row_html)
        
        print(f"   ✓ Procesados {error_count} errores del archivo")
        
        # Construir HTML tabla completa
        table_html = f"""
        <html>
        <body>
            <table>
                <tbody>
                    {''.join(html_rows)}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return table_html
        
    except Exception as e:
        print(f"   ⚠️ Error procesando archivo grande: {e}")
        # Retornar HTML vacío en caso de error
        return "<html><body><table><tbody></tbody></table></body></html>"
        
    finally:
        # Limpiar archivo temporal
        if temp_file.exists():
            try:
                temp_file.unlink()
                print(f"   🗑️ Archivo temporal eliminado: {temp_file.name}")
            except Exception as e:
                print(f"   ⚠️ Error eliminando archivo temporal: {e}")



def _fetch_logs_t4trans(session, fecha_str: str, app_key: str) -> str:
    """
    Fetches logs from T4TRANS which uses direct log file URLs.
    
    Unlike other Laravel apps that use encrypted token links (?l=...),
    T4TRANS provides direct links like: /t4notification/logs/laravel-2026-02-11.log
    """
    from urllib.parse import urljoin
    from bs4 import BeautifulSoup
    from datetime import datetime, timedelta
    from app.config import get_app_urls
    
    _, _, logs_url = get_app_urls(app_key)
    
    # Step 1: Get list of available log files
    resp_index = session.get(logs_url, timeout=60)
    resp_index.raise_for_status()
    
    soup = BeautifulSoup(resp_index.text, "html.parser")
    
    # Step 2: Find all links that contain .log
    log_links = [a for a in soup.find_all('a', href=True) if '.log' in a.get_text()]
    
    # Build target filename
    target_filename = f"laravel-{fecha_str}.log"
    
    # Find the link for the requested date
    link_tag = None
    for a in log_links:
        if a.get_text(strip=True) == target_filename:
            link_tag = a
            break
    
    # If not found, try previous day as fallback
    if link_tag is None:
        fecha_hoy = datetime.now().date()
        fecha_solicitada_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        
        # Don't use fallback for future dates
        if fecha_solicitada_obj > fecha_hoy:
            available_files = [a.get_text(strip=True) for a in log_links]
            msg = (
                f"⚠️ No se puede procesar fecha futura {fecha_str} en {app_key}. "
                f"Archivos disponibles: {available_files}"
            )
            raise RuntimeError(msg)
        
        # Try previous day
        fecha_anterior_obj = fecha_solicitada_obj - timedelta(days=1)
        fecha_anterior_str = fecha_anterior_obj.strftime("%Y-%m-%d")
        target_filename_anterior = f"laravel-{fecha_anterior_str}.log"
        
        print(f"   ⚠️ No se encontró log para {fecha_str}, intentando con {fecha_anterior_str}...")
        
        for a in log_links:
            if a.get_text(strip=True) == target_filename_anterior:
                link_tag = a
                print(f"   ✓ Usando logs del día anterior ({fecha_anterior_str})")
                break
    
    # If still not found, check for stale logs or error
    if link_tag is None:
        available_files = [a.get_text(strip=True) for a in log_links]
        
        # Check if logs are stale (2+ days old)
        most_recent_date, days_old = _get_most_recent_log_date_from_links(log_links)
        
        if most_recent_date and days_old >= 2:
            msg = (
                f"WARNING: Log files have not been created for two or more days in {app_key}. "
                f"Most recent log: {most_recent_date} ({days_old} days old). "
                f"Requested: {fecha_str}. Available files: {available_files}"
            )
            raise StaleLogsError(msg, app_key, fecha_str, days_old, most_recent_date)
        else:
            msg = (
                f"No se encontró log para {fecha_str} ni para el día anterior en {app_key}. "
                f"Archivos disponibles: {available_files}"
            )
            raise RuntimeError(msg)
    
    # Step 3: Get the direct URL from the link
    href = link_tag.get("href") or ""
    
    # The href can be absolute or relative
    if href.startswith('http'):
        log_file_url = href
    else:
        log_file_url = urljoin(logs_url, href)
    
    # Step 4: Fetch the log file content
    resp_day = session.get(log_file_url, timeout=60)
    resp_day.raise_for_status()
    logs_html = resp_day.text
    
    return logs_html


def _get_most_recent_log_date_from_links(log_links: list) -> tuple:
    """
    Extract the most recent date from a list of log file links.
    
    Args:
        log_links: List of BeautifulSoup <a> tag elements containing log filenames
        
    Returns:
        tuple: (most_recent_date, days_old) or (None, None) if no valid dates found
    """
    import re
    from datetime import datetime
    
    date_pattern = re.compile(r'laravel-(\d{4}-\d{2}-\d{2})\.log')
    log_dates = []
    
    for a in log_links:
        text = a.get_text(strip=True)
        match = date_pattern.match(text)
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


def classify_logs_t4trans(html: str):
    """
    Parser personalizado para T4TRANS.
    
    Clasificación actualizada:
    - local.ERROR → Errores NO CONTROLADOS
    - local.DEBUG con palabra "error" → Errores CONTROLADOS
    - local.DEBUG sin "error" → Ignorar
    
    Returns:
        (errores_controlados, errores_no_controlados) como listas de strings
    """
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html, "html.parser")
    
    errores_controlados = []
    errores_no_controlados = []
    
    # Obtener todo el texto del HTML
    page_text = soup.get_text()
    
    # Patrón más robusto para capturar entradas local.DEBUG o local.INFO
    # Captura timestamp y mensaje hasta el siguiente timestamp o fin de texto
    # El patrón maneja saltos de línea dentro del mensaje
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] local\.(DEBUG|INFO|ERROR|WARNING): (.*?)(?=\n\[|\Z)'
    
    matches = re.finditer(pattern, page_text, re.IGNORECASE | re.DOTALL)
    
    debug_count = 0
    error_count = 0
    
    for match in matches:
        timestamp = match.group(1)
        level = match.group(2).upper()
        message = match.group(3).strip()
        
        # Limpiar mensaje de saltos de línea excesivos
        message = ' '.join(message.split())
        
        # Si el mensaje está vacío, omitir
        if not message:
            continue
        
        # Clasificar según el nivel
        if level == "ERROR":
            # local.ERROR → NO CONTROLADO
            error_count += 1
            log_line = f"ERROR - local - {timestamp} - {message}"
            errores_no_controlados.append(log_line)
            
        elif level in ("DEBUG", "INFO"):
            # local.DEBUG o INFO → Solo si contiene "error" es CONTROLADO
            # Buscar la palabra "error" en diferentes formatos
            has_error_key = ('error' in message.lower() or 
                            '"error"' in message or 
                            '&quot;error&quot;' in message or 
                            '\\"error\\"' in message or 
                            '\"error\"' in message)
            
            if has_error_key:
                debug_count += 1
                log_line = f"ERROR - local - {timestamp} - {message}"
                errores_controlados.append(log_line)
            # Si no tiene "error", se ignora (no se agrega a ninguna lista)
    
    # Debug: imprimir contadores
    print(f"   ℹ️ T4TRANS parser: {error_count} local.ERROR (no controlados), {debug_count} local.DEBUG con 'error' (controlados)")
    
    return errores_controlados, errores_no_controlados


def classify_logs(html: str, app_key: str = None):
    """
    Parsea el HTML, se queda con Level = error,
    y los separa en controlados / no controlados.
    
    Si app_key es 't4trans', usa el parser personalizado.

    Devuelve (errores_controlados, errores_no_controlados) como listas de strings,
    donde cada string tiene el formato:
        ERROR - production - 2025-11-26 14:30:44 - Mensaje resumido
    """
    # Check if this app needs custom parsing
    if app_key == "t4trans":
        return classify_logs_t4trans(html)
    
    # Detect if app_key has custom auth_type
    if app_key:
        from app.config import APPS_CONFIG
        config = APPS_CONFIG.get(app_key, {})
        auth_type = config.get('auth_type', '')
        if auth_type == "t4trans_custom":
            return classify_logs_t4trans(html)
    
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

        level_lower = level.lower()
        content_lower = content.lower()
        
        is_error = level_lower == "error"
        is_info_with_error = level_lower == "info" and (
            '"error":' in content_lower or
            '&quot;error&quot;:' in content_lower or
            '\\"error\\":' in content_lower
        )

        # Solo nos interesan los que tienen Level = error o INFO con payload de error
        if not (is_error or is_info_with_error):
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
