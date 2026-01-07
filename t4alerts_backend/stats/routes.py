from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path to import from root project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import APPS_CONFIG
# Note: app.scrapper is imported on-demand in get_app_stats_logic to avoid circular imports

stats_bp = Blueprint('stats', __name__)
logger = logging.getLogger(__name__)

@stats_bp.route('/apps', methods=['GET'])
@jwt_required()
def get_apps():
    """
    Returns the list of configured applications for the accordion menu.
    """
    try:
        # Reload config dynamically to include any newly added apps in DB
        from app.config import get_apps_config
        current_config = get_apps_config()
        
        apps_list = []
        for key, config in current_config.items():
            apps_list.append({
                "key": key,
                "name": config.get("name", key),
                # Extra fields for Custom Scan autofill
                "base_url": config.get("base_url", ""),
                "login_path": config.get("login_path", "/login"),
                "logs_path": config.get("logs_path", "/logs"),
                "username": config.get("username", "") # Safe for admin
            })
        logger.info(f"Returning {len(apps_list)} apps")
        return jsonify(apps_list), 200
    except Exception as e:
        logger.error(f"Error fetching apps list: {e}")
        return jsonify({"error": str(e)}), 500

# Debug endpoint (no auth) for testing
@stats_bp.route('/debug/apps', methods=['GET'])
def debug_apps_list():
    """Debug endpoint to list available apps (Dynamic)."""
    try:
        # Reload config dynamically
        from app.config import get_apps_config
        current_config = get_apps_config()
        
        return jsonify({
            "status": "ok",
            "count": len(current_config),
            "apps": [{"key": k, "name": v.get("name", k)} for k, v in current_config.items()]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Debug endpoint for stats view (no auth) for testing
@stats_bp.route('/debug/view/<app_key>', methods=['GET'])
def debug_stats_view(app_key):
    """Debug endpoint without JWT to test stats functionality."""
    return get_app_stats_logic(app_key, request.args.get('date', datetime.now().strftime('%Y-%m-%d')))


@stats_bp.route('/view/<app_key>', methods=['GET'])
@jwt_required()
def get_app_stats(app_key):
    """
    Returns logs and statistics for a specific app and date.
    Reads from log files in salida_logs/ directory.
    Query Params: ?date=YYYY-MM-DD (default: today)
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    return get_app_stats_logic(app_key, date_str)


def get_app_stats_logic(app_key, date_str):
    """
    Core logic for fetching app stats via REAL-TIME SCRAPING.
    FALLBACK: If scraping fails (connection error), reads from .log files as backup.
    
    This provides best of both worlds:
    - Real-time data when servers are accessible
    - Cached data when servers are down or unreachable
    """
    try:
        # Convert date string to date object
        dia = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Reload config dynamically to ensure new apps are found
    from app.config import get_apps_config
    current_config = get_apps_config()
    
    if app_key not in current_config:
        return jsonify({"error": "App not found"}), 404

    # Try real-time scraping first
    try:
        logger.info(f"🔄 Starting REAL-TIME SCRAPING for {app_key} on {date_str}")
        
        from app.scrapper import procesar_aplicacion
        
        resultado = procesar_aplicacion(app_key, date_str, dia)
        
        logger.info(f"  ✓ Scraping completed for {app_key}")
        
        # DETAILED LOGGING - Show breakdown of new vs alerted
        logger.info(f"📊 DETAILED BREAKDOWN for {app_key} on {date_str}:")
        logger.info(f"  Controlled errors:")
        logger.info(f"    - Nuevos (new): {len(resultado['controlados_nuevos'])}")
        logger.info(f"    - Avisados (already alerted): {len(resultado['controlados_avisados'])}")
        logger.info(f"    - TOTAL: {len(resultado['controlados_nuevos']) + len(resultado['controlados_avisados'])}")
        logger.info(f"  Uncontrolled errors:")
        logger.info(f"    - Nuevos (new): {len(resultado['no_controlados_nuevos'])}")
        logger.info(f"    - Avisados (already alerted): {len(resultado['no_controlados_avisados'])}")
        logger.info(f"    - TOTAL: {len(resultado['no_controlados_nuevos']) + len(resultado['no_controlados_avisados'])}")
        
        # Get ALL errors (new + previously alerted)
        controlados_all = resultado['controlados_nuevos'] + resultado['controlados_avisados']
        no_controlados_all = resultado['no_controlados_nuevos'] + resultado['no_controlados_avisados']
        
        # Convert strings to dict format for aggregation
        # Each error line is a string, but agregar_errores_por_firma expects dicts with 'firma' field
        from app.signatures import build_signature
        
        def convert_to_dict_format(error_lines, dia):
            """Convert list of error strings to list of dicts with firma field"""
            result = []
            for line in error_lines:
                firma = build_signature(line)
                result.append({
                    'firma': firma,
                    'timestamp': datetime.combine(dia, datetime.min.time())
                })
            return result
        
        controlados_dict = convert_to_dict_format(controlados_all, dia)
        no_controlados_dict = convert_to_dict_format(no_controlados_all, dia)
        
        # Aggregate by signature
        nc_aggregated = agregar_errores_por_firma(no_controlados_dict, dia)
        c_aggregated = agregar_errores_por_firma(controlados_dict, dia)
        
        logger.info(f"  • Unique NC signatures: {len(nc_aggregated)}")
        logger.info(f"  • Unique C signatures: {len(c_aggregated)}")
        
        # Format for frontend
        uncontrolled_logs = format_errors_for_frontend(nc_aggregated)
        controlled_logs = format_errors_for_frontend(c_aggregated)
        
        # Calculate SQL stats
        sql_count = 0
        non_sql_count = 0
        
        for err in nc_aggregated:
            if es_error_sql(err['firma']):
                sql_count += err['count']
            else:
                non_sql_count += err['count']
        
        logger.info(f"  • SQL errors: {sql_count}, Non-SQL: {non_sql_count}")
        
        # Extract SQLSTATE distribution for bar chart
        sqlstate_dist = extract_sqlstate_distribution(nc_aggregated)
        logger.info(f"  • SQLSTATE distribution: {len(sqlstate_dist)} unique codes")
        
        response_data = {
            "logs": {
                "uncontrolled": uncontrolled_logs,
                "controlled": controlled_logs
            },
            "stats": {
                "sqlstate_distribution": sqlstate_dist,
                "sql_errors": sql_count,  # Keep for backward compatibility
                "non_sql_errors": non_sql_count
            },
            "source": "real-time-scraping"
        }
        
        # FINAL LOG - What we're actually sending to frontend
        logger.info(f"📤 SENDING TO FRONTEND:")
        logger.info(f"  - Uncontrolled logs: {len(uncontrolled_logs)} unique signatures")
        logger.info(f"  - Controlled logs: {len(controlled_logs)} unique signatures")
        logger.info(f"  - SQL errors: {sql_count}, Non-SQL: {non_sql_count}")
        logger.info(f"  - SQLSTATE codes: {[s['sqlstate'] for s in sqlstate_dist]}")
        
        return jsonify(response_data), 200
        
    except Exception as scraping_error:
        # FALLBACK: If scraping fails, try to read from .log files
        logger.warning(f"⚠️ Scraping failed for {app_key}, trying fallback to .log files...")
        logger.warning(f"   Error was: {str(scraping_error)[:200]}")
        
        try:
            # Calculate project root and try reading from files
            project_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            LOG_DIR = project_root / "salida_logs"
            
            # Add app_key suffix
            no_controlados_path = LOG_DIR / f"errores_no_controlados_{app_key}.log"
            controlados_path = LOG_DIR / f"errores_controlados_{app_key}.log"
            
            logger.info(f"  📂 Trying to read from: {no_controlados_path.name}")
            
            # Import the file-reading function
            from app.log_stats import get_daily_errors
            
            # Get errors for the day
            nc_errors = get_daily_errors(no_controlados_path, dia)
            c_errors = get_daily_errors(controlados_path, dia)
            
            logger.info(f"  ✓ Fallback successful - found {len(nc_errors)} NC, {len(c_errors)} C from files")
            
            # Format for frontend (same as scraping path)
            def format_errors(errors):
                formatted = []
                for err in errors:
                    formatted.append({
                        "timestamp": err["first_time"].strftime('%Y-%m-%d %H:%M:%S'),
                        "message": err["firma"],
                        "count": err["count"]
                    })
                return formatted
            
            uncontrolled_logs = format_errors(nc_errors)
            controlled_logs = format_errors(c_errors)
            
            # Calculate SQL stats
            sql_count = 0
            non_sql_count = 0
            
            for err in nc_errors:
                if es_error_sql(err["firma"]):
                    sql_count += err["count"]
                else:
                    non_sql_count += err["count"]
            
            response_data = {
                "logs": {
                    "uncontrolled": uncontrolled_logs,
                    "controlled": controlled_logs
                },
                "stats": {
                    "sql_errors": sql_count,
                    "non_sql_errors": non_sql_count
                },
                "source": "cached-files",
                "note": f"Real-time scraping failed, showing cached data from {date_str}"
            }
            
            return jsonify(response_data), 200
            
        except Exception as fallback_error:
            # Both scraping AND file reading failed
            logger.error(f"❌ Both scraping and fallback failed for {app_key}")
            logger.error(f"   Scraping error: {str(scraping_error)[:100]}")
            logger.error(f"   Fallback error: {str(fallback_error)[:100]}")
            
            return jsonify({
                "error": f"Unable to fetch stats", 
                "details": {
                    "scraping_failed": str(scraping_error)[:200],
                    "cache_failed": str(fallback_error)[:200]
                },
                "suggestion": "Server may be down. Try again later or run main.py to update cache."
            }), 500


def agregar_errores_por_firma(errores_lista, dia):
    """
    Agrupa errores por firma (signature) y cuenta recurrencias.
    
    Args:
        errores_lista: Lista de dicts con 'firma', 'timestamp', etc.
        dia: fecha del día (para defaults)
    
    Returns:
        Lista de dicts: [{firma: str, count: int, first_time: datetime}, ...]
        Ordenados por tiempo de primera aparición
    """
    from collections import defaultdict
    
    agregado = defaultdict(lambda: {'count': 0, 'first_time': None})
    
    for error in errores_lista:
        firma = error.get('firma', 'Unknown error')
        
        # El timestamp puede venir de diferentes campos según la fuente
        timestamp = error.get('timestamp') or error.get('fecha') or datetime.combine(dia, datetime.min.time())
        
        agregado[firma]['count'] += 1
        
        # Guardar timestamp más temprano
        if agregado[firma]['first_time'] is None or timestamp < agregado[firma]['first_time']:
            agregado[firma]['first_time'] = timestamp
    
    # Convertir a lista
    result = []
    for firma, data in agregado.items():
        result.append({
            'firma': firma,
            'count': data['count'],
            'first_time': data['first_time'] or datetime.combine(dia, datetime.min.time())
        })
    
    # Ordenar por tiempo de primera aparición
    result.sort(key=lambda x: x['first_time'])
    
    return result


def format_errors_for_frontend(aggregated_errors):
    """
    Formatea errores agregados para el frontend.
    
    Args:
        aggregated_errors: Lista de dicts con firma, count, first_time
    
    Returns:
        Lista de dicts con timestamp, message, count (formato esperado por JS)
    """
    formatted = []
    for err in aggregated_errors:
        formatted.append({
            "timestamp": err["first_time"].strftime('%Y-%m-%d %H:%M:%S'),
            "message": err["firma"],
            "count": err["count"]
        })
    return formatted


def extract_sqlstate_distribution(aggregated_errors):
    """
    Extrae y agrupa errores por código SQLSTATE.
    
    Args:
        aggregated_errors: Lista de errores con firma, count, first_time
    
    Returns:
        Lista ordenada por first_time: [
            {
                'sqlstate': 'SQLSTATE[40001]',
                'count': 3,
                'first_time': '2025-12-21 01:00:41'
            },
            ...
        ]
    """
    import re
    from collections import defaultdict
    
    # Pattern para extraer SQLSTATE[XXXXX]
    pattern = re.compile(r'SQLSTATE\[\w+\]')
    
    sqlstate_data = defaultdict(lambda: {'count': 0, 'first_time': None})
    
    for error in aggregated_errors:
        firma = error['firma']
        match = pattern.search(firma)
        
        if match:
            sqlstate = match.group(0)
            sqlstate_data[sqlstate]['count'] += error['count']
            
            # Guardar el timestamp más temprano
            if sqlstate_data[sqlstate]['first_time'] is None or \
               error['first_time'] < sqlstate_data[sqlstate]['first_time']:
                sqlstate_data[sqlstate]['first_time'] = error['first_time']
    
    # Convertir a lista y ordenar por first_time
    result = []
    for sqlstate, data in sqlstate_data.items():
        result.append({
            'sqlstate': sqlstate,
            'count': data['count'],
            'first_time': data['first_time'].strftime('%Y-%m-%d %H:%M:%S') if data['first_time'] else None
        })
    
    # Ordenar por tiempo de primera aparición
    result.sort(key=lambda x: x['first_time'] if x['first_time'] else '')
    
    return result


def es_error_sql(mensaje):
    """
    Detecta si un error es de tipo SQL.
    Usa los mismos keywords que sms_notifier para consistencia.
    
    Args:
        mensaje: texto del mensaje de error
    
    Returns:
        bool: True si es error SQL, False si no
    """
    msg_upper = mensaje.upper()
    return any(keyword in msg_upper for keyword in ['SQL', 'SQLSTATE', 'DATABASE', 'PDO'])
@stats_bp.route('/send-email', methods=['POST'])
@jwt_required()
def send_error_email_endpoint():
    """
    Manually triggers an email notification for a specific error.
    Body:
    {
        "app_key": "driverapp_goto", // Optional if subject is full
        "recipients": ["user@example.com"],
        "subject": "Custom Subject",
        "body": "Custom Body"
    }
    """
    try:
        data = request.get_json()
        recipients = data.get('recipients')
        subject = data.get('subject')
        body = data.get('body')
        
        if not recipients or not subject or not body:
            return jsonify({'error': 'Missing required fields (recipients, subject, or body)'}), 400
            
        # Ensure recipients is a list
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(',')]
            
        # Clean up empty strings
        recipients = [r for r in recipients if r]
        
        if not recipients:
             return jsonify({'error': 'No valid recipients provided'}), 400

        # Import sender dynamically with correct path check
        try:
            from app.alerts import send_email
        except ImportError:
            # Fallback for when running from different contexts
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from app.alerts import send_email
        
        # Format body as HTML 
        # We trust the frontend to send properly formatted HTML with styles
        html_body = body
        
        # Send
        # send_email(subject, html_body, to_addrs, sender_name=None)
        send_email(subject, html_body, recipients)
        
        # Note: send_email does not return success/fail boolean, it logs internally. 
        # We assume success if no exception raised.
        
        logger.info(f"📧 Manual email sent to {recipients}")
        return jsonify({'message': 'Email sent successfully', 'recipients': recipients}), 200
            
    except Exception as e:
        logger.error(f"Error in send-email endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@stats_bp.route('/scan-adhoc', methods=['POST'])
@jwt_required()
def scan_adhoc():
    """
    Realiza un escaneo bajo demanda para una aplicación no registrada.
    """
    logger.info("⚡ RECEIVED SCAN-ADHOC REQUEST")
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['base_url', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        base_url = data['base_url']
        login_path = data.get('login_path', '/login')
        logs_path = data.get('logs_path', '/logs')
        username = data['username']
        password = data['password']
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        logger.info(f"Ad-hoc scan requested for {base_url} on {date_str}")
        
        # Import scraping function
        from app.scrapper import procesar_aplicacion
        from app.config import APPS_CONFIG
        from datetime import date
        
        # Parse date
        try:
            dia = date.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': f'Invalid date format: {date_str}. Use YYYY-MM-DD'}), 400
        
        # Create temporary app key
        temp_app_key = f"adhoc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Temporarily inject into APPS_CONFIG
        APPS_CONFIG[temp_app_key] = {
            "name": f"Ad-Hoc Scan: {base_url}",
            "base_url": base_url,
            "login_path": login_path,
            "logs_path": logs_path,
            "username": username,
            "password": password,
        }
        
        try:
            # Execute scraping
            resultado = procesar_aplicacion(temp_app_key, date_str, dia)
            
            # Format response (same as /view endpoint)
            uncontrolled_errors = resultado.get('no_controlados_nuevos', []) + resultado.get('no_controlados_avisados', [])
            controlled_errors = resultado.get('controlados_nuevos', []) + resultado.get('controlados_avisados', [])
            
            response = {
                'logs': uncontrolled_errors,
                'controlled': controlled_errors,
                'app_key': temp_app_key,
                'date': date_str
            }
            
            logger.info(f"Ad-hoc scan completed for {base_url}: {len(uncontrolled_errors)} uncontrolled, {len(controlled_errors)} controlled")
            return jsonify(response), 200
            
        finally:
            # Clean up temporary config
            APPS_CONFIG.pop(temp_app_key, None)
    
    except Exception as e:
        logger.error(f"Error in ad-hoc scan: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
