# app/email_notifier.py
from datetime import date, datetime
from pathlib import Path
from typing import List, Tuple

from .alerts import send_email, default_recipients
from .log_stats import (
    resumen_por_fecha,
    url_logs_para_dia,
)

# Rutas base (sin sufijo de app)
LOG_DIR = Path("salida_logs")
NO_CONTROLADOS_BASE = LOG_DIR / "errores_no_controlados.log"
CONTROLADOS_BASE = LOG_DIR / "errores_controlados.log"


def _get_log_paths(app_key: str):
    """
    Retorna las rutas de logs para una app específica.
    
    Args:
        app_key: clave de la aplicación
    
    Returns:
        (ruta_no_controlados, ruta_controlados)
    """
    if '.' in str(NO_CONTROLADOS_BASE):
        base_nc, ext_nc = str(NO_CONTROLADOS_BASE).rsplit('.', 1)
        base_c, ext_c = str(CONTROLADOS_BASE).rsplit('.', 1)
        no_controlados_path = Path(f"{base_nc}_{app_key}.{ext_nc}")
        controlados_path = Path(f"{base_c}_{app_key}.{ext_c}")
    else:
        no_controlados_path = Path(f"{NO_CONTROLADOS_BASE}_{app_key}")
        controlados_path = Path(f"{CONTROLADOS_BASE}_{app_key}")
    
    return no_controlados_path, controlados_path




def _formatear_mensaje_sql(mensaje: str) -> str:
    """
    Detecta mensajes de error SQL y resalta en negrita y rojo la parte específica del error.
    
    Por ejemplo, en:
    "SQL0911N The current transaction has been rolled back... SQLSTATE=40001"
    
    Resalta en rojo: "The current transaction has been rolled back..."
    que está entre SQL0911N y SQLSTATE
    
    Args:
        mensaje: texto del mensaje de error
    
    Returns:
        mensaje formateado con HTML si es SQL, o el mensaje original
    """
    import re
    
    # Patrón para detectar errores SQL: SQL seguido de dígitos y letra N, luego texto, luego SQLSTATE
    # Ejemplos: SQL30081N, SQL0911N, SQL0803N
    patron = r'(SQL\d+N)\s+(.*?)\s+(SQLSTATE[=\[])'
    
    def reemplazar_match(match):
        codigo_sql = match.group(1)  # Ej: SQL0911N
        mensaje_error = match.group(2)  # El mensaje específico
        sqlstate = match.group(3)  # SQLSTATE= o SQLSTATE[
        
        # Resaltar el mensaje de error en rojo y negrita
        return f'{codigo_sql} <strong style="color: red;">{mensaje_error}</strong> {sqlstate}'
    
    # Aplicar el reemplazo
    mensaje_formateado = re.sub(patron, reemplazar_match, mensaje)
    
    return mensaje_formateado


def _html_lista_errores(titulo: str, errors: List[dict], empty_msg: str = "Sin elementos.") -> str:
    """
    Formato genérico de lista de errores:
    HEADER
    YYYY-MM-DD HH:MM:SS — Error msg (xN)
    """
    if not errors:
        return f"<h3>{titulo}</h3><p>{empty_msg}</p>"

    lineas = [f"<h3>{titulo}</h3>", "<ul>"]
    for err in errors:
        fecha_str = err["first_time"].strftime("%Y-%m-%d %H:%M:%S")
        firma_formateada = _formatear_mensaje_sql(err["firma"])
        
        count_suffix = ""
        # Mostrar cuenta, en negrita: (xN)
        # O si el usuario prefiere "colocar al final la cantidad de veces que se repite, en negrita, por ejemplo x2"
        # Asumo siempre mostramos la cantidad si > 1, o incluso si es 1 para consistencia?
        # El ejemplo dice: "The current... (colocar al final la cantidad..., por ejemplo x2)"
        # Si es 1 vez, quizá queda mejor no poner nada o poner (x1). Pondré (xN) siempre para ser claro, o solo si > 1.
        # El request dice: "colocar al final la cantidad de veces que se repite, en negrita, por ejemplo x2" 
        # Lo haré para todos.
        
        lineas.append(f"<li><strong>{fecha_str}</strong> — {firma_formateada} <strong>(x{err['count']})</strong></li>")
        
    lineas.append("</ul>")
    return "\n".join(lineas)


def construir_html_resumen(dia: date, app_name: str = "DriverApp GO2", app_key: str = "driverapp_goto") -> tuple[str, int, int]:
    """
    Construye el HTML del resumen de errores con el nuevo formato.
    
    Args:
        dia: fecha del reporte
        app_name: nombre de la aplicación
        app_key: clave de la aplicación
    
    Returns:
        (html_content, total_no_controlados, total_controlados)
    """
    from .log_stats import get_daily_errors
    
    # Obtener rutas específicas de la app
    no_controlados_path, controlados_path = _get_log_paths(app_key)
    
    # Usar get_daily_errors
    nc_errors = get_daily_errors(no_controlados_path, dia)
    c_errors = get_daily_errors(controlados_path, dia)
    
    total_nc = sum(e["count"] for e in nc_errors)
    total_c = sum(e["count"] for e in c_errors)

    url_logs = url_logs_para_dia(dia, app_key)

    # Construir HTML
    # Formato Header: Company: GoTo Logistics — 2025-12-11
    # Antes era azul, ahora negro (sin style color o color: black).
    
    # Mapping de nombres para el header
    display_names = {
        "driverapp_goto": "Go 2 Logistics",
        "klc_crossdock": "KLC Crossdock",
    }
    display_name = display_names.get(app_key, app_name)
    
    header = f'<h2>Company: {display_name} — {dia.isoformat()}</h2>'
    
    # "Errores (no controlados)" pasa a ser "Errores" y en rojo.
    # "Errores (controlados)" se mantiene el texto (creo, el user dijo "donde dice Errores (controlados), ese subtitulo cambialo a color azul")
    # pero para el primero dijo "donde dice Errores (no controlados), ahora debe decir Errores"
    
    html_nc = _html_lista_errores('<span style="color: red;">Errors</span>', nc_errors, empty_msg="No items.")
    html_c = _html_lista_errores('<span style="color: blue;">Errors (controlled)</span>', c_errors, empty_msg="No updates.")
    
    partes = [
        header,
        html_nc,
        html_c,
        f'<p>More details: <a href="{url_logs}">{url_logs}</a></p>',
    ]

    return "\n".join(partes), total_nc, total_c


def _get_subject(app_key: str, dia: date) -> str:
    """
    Genera el asunto del correo según app_key.
    Formato: 🔥 [Prefix - Name] Errores YYYY-MM-DD
    """
    date_str = dia.isoformat()
    
    # Mapping personalizado
    # driverapp_goto -> [DRIVERAPP - GO 2 LOGISTICS]
    # goexperior    -> [DRIVERAPP - GOEXPERIOR]
    # accuratecargo -> [T4APP - ACCURATECARGO]
    # klc           -> [T4APP - KLC]
    # broker_goto   -> [BROKER - GO 2 LOGISTICS]
    
    subjects = {
        "driverapp_goto": f"[DRIVERAPP - GO 2 LOGISTICS] Errors {date_str}",
        "goexperior": f"[DRIVERAPP - GOEXPERIOR] Errors {date_str}",
        "accuratecargo": f"[T4APP - ACCURATECARGO] Errors {date_str}",
        "klc": f"[T4APP - KLC] Errors {date_str}",
        "broker_goto": f"[BROKER - GO 2 LOGISTICS] Errors {date_str}",
        "klc_crossdock": f"[T4APP - KLC CROSSDOCK] Errors {date_str}",
        "t4tms_backend": f"[T4TMS - BACKEND] Errors {date_str}",
    }
    
    # Fallback genérico si agregamos nuevas apps
    fallback_key = app_key.replace("_", " ").upper()
    base = subjects.get(app_key, f"[{fallback_key}] Errors {date_str}")
    
    return f"🔥 {base}"


def _get_sender_name(app_key: str, subject: str) -> str:
    """
    Determina el nombre del remitente basado en la app.
    """
    sender_name = "driverapp-logs" # Default
    
    # Caso especial para KLC Crossdock y T4TMS Backend
    if app_key == "klc_crossdock":
        sender_name = "klc-crossdock-logs"
    elif app_key == "t4tms_backend":
        sender_name = "t4tms"
    elif "T4APP" in subject:
        sender_name = "t4app-logs"
    elif "BROKER" in subject:
        sender_name = "broker-logs"
    elif "DRIVERAPP" in subject:
        sender_name = "driverapp-logs"
        
    return sender_name


def enviar_resumen_por_correo(dia: date, app_name: str = "DriverApp GO2", app_key: str = "driverapp_goto") -> None:
    """
    Envía el resumen de errores por correo.
    
    Args:
        dia: fecha del reporte
        app_name: nombre de la aplicación
        app_key: clave de la aplicación
    """
    html, total_nc, total_c = construir_html_resumen(dia, app_name, app_key)

    # Si no hay errores no controlados, no enviamos nada (ignoramos los controlados)
    if total_nc == 0:
        return

    subject = _get_subject(app_key, dia)
    sender_name = _get_sender_name(app_key, subject)

    recipients = default_recipients()  # usa ALERT_EMAIL_TO o MAIL_USERNAME

    send_email(subject, html, recipients, sender_name=sender_name)
