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


def _html_lista_repetidos(titulo: str, items: List[Tuple[str, int]]) -> str:
    """
    Formato para repetidos:
    NO lleva fecha al inicio.
    Lleva count al final, dentro de paréntesis.
    """
    if not items:
        return f"<h3>{titulo}</h3><p>Sin elementos.</p>"

    lineas = [f"<h3>{titulo}</h3>", "<ul>"]
    for firma, count in items:
        # Mostrar contenido completo sin truncar y formatear SQL
        firma_formateada = _formatear_mensaje_sql(firma)
        lineas.append(f"<li>{firma_formateada} <strong>({count} veces)</strong></li>")
    lineas.append("</ul>")
    return "\n".join(lineas)


def _html_lista_nuevos(titulo: str, items: List[Tuple[str, datetime]]) -> str:
    """
    Formato para nuevos:
    Lleva fecha al inicio.
    NO lleva count.
    """
    if not items:
        return f"<h3>{titulo}</h3><p>Sin elementos.</p>"

    lineas = [f"<h3>{titulo}</h3>", "<ul>"]
    for firma, first_dt in items:
        fecha_str = first_dt.strftime("%Y-%m-%d %H:%M:%S")
        # Mostrar contenido completo sin truncar y formatear SQL
        firma_formateada = _formatear_mensaje_sql(firma)
        lineas.append(f"<li><strong>{fecha_str}</strong> — {firma_formateada}</li>")
    lineas.append("</ul>")
    return "\n".join(lineas)


def construir_html_resumen(dia: date, app_name: str = "DriverApp GO2", app_key: str = "driverapp_goto") -> tuple[str, int, int]:
    """
    Construye el HTML del resumen de errores.
    
    Args:
        dia: fecha del reporte
        app_name: nombre de la aplicación (ej: "DriverApp GoTo Logistics")
        app_key: clave de la aplicación para obtener URLs y logs
    
    Returns:
        (html_content, total_no_controlados, total_controlados)
    """
    # Obtener rutas específicas de la app
    no_controlados_path, controlados_path = _get_log_paths(app_key)
    
    total_nc, repetidos_nc, nuevos_nc = resumen_por_fecha(no_controlados_path, dia)
    total_c, repetidos_c, nuevos_c = resumen_por_fecha(controlados_path, dia)

    url_logs = url_logs_para_dia(dia, app_key)

    partes = [
        f'<h2 style="color: blue;">Resumen de errores {app_name} — {dia.isoformat()}</h2>',
        _html_lista_repetidos("NO controlados repetidos hoy (>=3 veces)", repetidos_nc),
        _html_lista_nuevos("NO controlados - Primer horario de aparicion", nuevos_nc),
        f'<p>Más detalles: <a href="{url_logs}">{url_logs}</a></p>',
    ]

    return "\n".join(partes), total_nc, total_c


def enviar_resumen_por_correo(dia: date, app_name: str = "DriverApp GO2", app_key: str = "driverapp_goto") -> None:
    """
    Envía el resumen de errores por correo.
    
    Args:
        dia: fecha del reporte
        app_name: nombre de la aplicación (ej: "DriverApp GoTo Logistics")
        app_key: clave de la aplicación para obtener URLs
    """
    html, total_nc, total_c = construir_html_resumen(dia, app_name, app_key)

    # Si no hay errores no controlados, no enviamos nada (ignoramos los controlados)
    if total_nc == 0:
        return

    subject = f"[{app_name}] Errores {dia.isoformat()} — NC:{total_nc} / C:{total_c}"

    recipients = default_recipients()  # usa ALERT_EMAIL_TO o MAIL_USERNAME

    send_email(subject, html, recipients)
