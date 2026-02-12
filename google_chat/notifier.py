# google_chat/notifier.py
"""
Notification functions for Google Chat integration with T4Alerts
These functions are called from app/notifier.py
"""

from typing import Dict, Any
from datetime import date
from pathlib import Path
import logging

from google_chat.config import get_gchat_config
from google_chat.auth import ChatAuthConfig
from google_chat.client import GoogleChatClient
from google_chat.errors import ChatAPIError

# Set up logger
logger = logging.getLogger(__name__)

# Log paths (same as email_notifier.py)
LOG_DIR = Path("salida_logs")
NO_CONTROLADOS_BASE = LOG_DIR / "errores_no_controlados.log"
CONTROLADOS_BASE = LOG_DIR / "errores_controlados.log"


def _get_log_paths(app_key: str):
    """
    Returns log paths for a specific app.
    
    Args:
        app_key: application key
    
    Returns:
        (no_controlados_path, controlados_path)
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


def _get_thread_key(app_key: str, strategy: str) -> str:
    """
    Generate thread key based on strategy
    
    Args:
        app_key: Application key (e.g., "driverapp_goto")
        strategy: Threading strategy ("per_app", "per_error_type", "per_date", "none")
    
    Returns:
        Thread key string
    """
    if strategy == "per_app":
        return f"app-{app_key}"
    elif strategy == "none":
        return None
    else:
        # For other strategies, use app_key as default
        return f"app-{app_key}"


def _format_error_message_email_style(app_name: str, app_key: str, dia: date, nc_errors: list, c_errors: list) -> str:
    """
    Format error message for Google Chat using the same format as emails.
    
    Format:
    Company: T4APP - KLC — 2026-02-03
    Errors
    2026-02-03 00:00:04 — error message (x305)
    ...
    Errors (controlled)
    2026-02-03 00:00:03 — error message (x305)
    ...
    Para ver más detalles: [url]
    
    Args:
        app_name: Application display name
        app_key: Application key for URL generation
        dia: Date
        nc_errors: List of uncontrolled errors from get_daily_errors()
        c_errors: List of controlled errors from get_daily_errors()
    
    Returns:
        Formatted message string, or None if no uncontrolled errors
    """
    # Only send if there are uncontrolled errors (avoid spam from controlled-only errors)
    if not nc_errors:
        return None
    
    lines = []
    
    # Header: Company: T4APP - KLC — 2026-02-03
    lines.append(f"**Company: {app_name} — {dia.isoformat()}**")
    lines.append("")
    
    # Errors section (uncontrolled)
    lines.append("**Errors**")
    for err in nc_errors[:20]:  # Limit to 20 to avoid message size limits
        fecha_str = err["first_time"].strftime("%Y-%m-%d %H:%M:%S")
        firma = err["firma"]
        
        # Truncate very long error messages for Google Chat
        if len(firma) > 200:
            firma = firma[:197] + "..."
        
        lines.append(f"`{fecha_str}` — {firma} **(x{err['count']})**")
    
    if len(nc_errors) > 20:
        lines.append(f"_...y {len(nc_errors) - 20} errores más_")
    
    # Errors (controlled) section - only if there are any
    if c_errors:
        lines.append("")
        lines.append("**Errors (controlled)**")
        for err in c_errors[:10]:  # Limit controlled errors to 10
            fecha_str = err["first_time"].strftime("%Y-%m-%d %H:%M:%S")
            firma = err["firma"]
            
            # Truncate very long error messages
            if len(firma) > 200:
                firma = firma[:197] + "..."
            
            lines.append(f"`{fecha_str}` — {firma} **(x{err['count']})**")
        
        if len(c_errors) > 10:
            lines.append(f"_...y {len(c_errors) - 10} errores controlados más_")
    
    # Add logs URL at the end
    from app.log_stats import url_logs_para_dia
    logs_url = url_logs_para_dia(dia, app_key)
    
    lines.append("")
    lines.append(f"📋 Para ver más detalles: {logs_url}")
    
    return "\n".join(lines)


def enviar_gchat_errores_no_controlados(resultado: Dict[str, Any]) -> bool:
    """
    Send Google Chat notification for uncontrolled errors
    Called from app/notifier.py
    
    Uses the same format as email notifications with timestamps and counts.
    
    Args:
        resultado: Result dict from procesar_aplicacion() with keys:
            - app_name: Application name
            - app_key: Application key
            - dia: Date string or date object
    
    Returns:
        True if notification was sent, False otherwise
    """
    try:
        # Get configuration
        config = get_gchat_config()
        
        if not config["enabled"]:
            return False
        
        # Import here to avoid circular dependencies
        from app.log_stats import get_daily_errors
        
        # Get data
        app_name = resultado.get("app_name", "Unknown")
        app_key = resultado.get("app_key", "unknown")
        dia = resultado.get("dia")
        
        # Convert dia to date if it's a string
        if isinstance(dia, str):
            from datetime import datetime
            dia = datetime.strptime(dia, "%Y-%m-%d").date()
        
        # Get log paths and read errors (same as email)
        no_controlados_path, controlados_path = _get_log_paths(app_key)
        nc_errors = get_daily_errors(no_controlados_path, dia)
        c_errors = get_daily_errors(controlados_path, dia)
        
        # Format message
        message = _format_error_message_email_style(app_name, app_key, dia, nc_errors, c_errors)
        
        if not message:
            # No uncontrolled errors
            return False
        
        # Get thread key
        thread_key = _get_thread_key(app_key, config["thread_strategy"])
        
        # Initialize client and send
        auth_config = ChatAuthConfig(mode=config["mode"])
        client = GoogleChatClient(auth_config)
        
        client.send_text(
            space_name=config["space_name"],
            text=message,
            thread_key=thread_key
        )
        
        return True
        
    except ChatAPIError as e:
        logger.error(f"Google Chat API error: {e}")
        print(f"DEBUG - Google Chat API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending Google Chat notification: {e}")
        print(f"DEBUG - Error sending Google Chat: {e}")
        import traceback
        traceback.print_exc()
        return False


def enviar_aviso_gchat(mensaje: str) -> bool:
    """
    Send a general notification to Google Chat
    Used for warnings (future dates, stale logs, etc.)
    
    Args:
        mensaje: Message text to send
    
    Returns:
        True if notification was sent, False otherwise
    """
    try:
        # Get configuration
        config = get_gchat_config()
        
        if not config["enabled"]:
            return False
        
        # Initialize client and send
        auth_config = ChatAuthConfig(mode=config["mode"])
        client = GoogleChatClient(auth_config)
        
        # Send to general thread or no thread
        thread_key = "avisos" if config["thread_strategy"] != "none" else None
        
        client.send_text(
            space_name=config["space_name"],
            text=mensaje,
            thread_key=thread_key
        )
        
        return True
        
    except ChatAPIError as e:
        logger.error(f"Google Chat API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending Google Chat notification: {e}")
        return False
