from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from t4alerts_backend.notifications.models import NotificationSettings
from t4alerts_backend.common.database import db
import logging
from mailer.client import send_email

notifications_bp = Blueprint('notifications', __name__)
logger = logging.getLogger(__name__)

@notifications_bp.route('/settings/<app_key>', methods=['GET'])
@jwt_required()
def get_settings(app_key):
    try:
        settings = NotificationSettings.query.filter_by(app_key=app_key).first()
        if not settings:
            return jsonify({'recipients': [], 'schedule_enabled': False, 'schedule_interval_hours': 24}), 200
        return jsonify(settings.to_dict()), 200
    except Exception as e:
        logger.error(f"Error fetching notification settings: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/settings/<app_key>', methods=['POST'])
@jwt_required()
def save_settings(app_key):
    try:
        data = request.get_json()
        settings = NotificationSettings.query.filter_by(app_key=app_key).first()
        
        if not settings:
            settings = NotificationSettings(app_key=app_key)
            db.session.add(settings)
            
        settings.recipients = data.get('recipients', [])
        settings.schedule_enabled = data.get('schedule_enabled', False)
        settings.schedule_interval_hours = data.get('schedule_interval_hours', 24)
        
        db.session.commit()
        return jsonify({'message': 'Settings saved', 'settings': settings.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving notification settings: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/send', methods=['POST'])
@jwt_required()
def send_manual_notice():
    """
    Trigger a manual notice.
    If recipients provided in body, use them.
    Otherwise, use saved settings.
    Wrapper supports 'use_template' to generate standard report.
    Uses Streaming Response to avoid 504 Gateway Timeout.
    """
    from flask import Response, stream_with_context, current_app
    import json
    import time
    from concurrent.futures import ThreadPoolExecutor
    
    # Capture data eagerly
    try:
        data = request.get_json()
    except Exception as e:
        return jsonify({'error': 'Invalid JSON'}), 400

    def generate():
        # Flush buffer immediately with 2KB of spaces
        yield " " * 2048
        
        # Setup Executor
        executor = ThreadPoolExecutor(max_workers=1)
        
        # Capture real app object to pass context to thread
        app = current_app._get_current_object()
        
        def run_logic():
            with app.app_context():
                try:
                    app_key = data.get('app_key')
                    subject = data.get('subject')
                    body = data.get('body')
                    recipients = data.get('recipients') # Optional override
                    use_template = data.get('use_template', False)
                    date_str = data.get('date') # Required if use_template is True
                    
                    if not app_key:
                        return {'error': 'Missing required fields: app_key', 'status': 400}
                        
                    if not recipients:
                        # Fallback to saved settings
                        settings = NotificationSettings.query.filter_by(app_key=app_key).first()
                        if settings and settings.recipients:
                            recipients = settings.recipients
                    
                    if not recipients:
                        return {'error': 'No recipients provided or found in settings', 'status': 400}
            
                    # Generate Body from Template if requested
                    if use_template:
                        if not date_str:
                            return {'error': 'Date is required when using template', 'status': 400}
                            
                        from datetime import datetime
                        try:
                            dia = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            return {'error': 'Invalid date format', 'status': 400}
            
                        # Get app name
                        from app.config import get_apps_config
                        # Ensure we look at dynamic content too
                        cfg = get_apps_config(dynamic_only=False, quiet=True).get(app_key, {})
                        app_name = cfg.get('name', app_key)
                        
                        # TRIGGER SCRAPING: To match main.py, we must ensure logs are scraped.
                        resultado = None
                        try:
                            from app.scrapper import procesar_aplicacion
                            # We reuse the same logic
                            logger.info(f"🔄 [Manual Trigger] Scraping logs for {app_key} on {dia}")
                            # Use robust settings to match main.py
                            resultado = procesar_aplicacion(app_key, date_str, dia, max_retries=3, timeout=60)
                        except Exception as e:
                            logger.error(f"Error during manual scraping for {app_key}: {e}")
                            # Continue with partial data or fail? 
                            # If connection error, we might want to report it, but let's try to proceed
                            # Actually, if scraping fails completely, the report will be empty.
                            
                        # Generate HTML
                        from mailer.builder import construir_html_resumen, _get_subject
                        try:
                            forced_data = None
                            if resultado:
                                from app.log_stats import parse_and_aggregate_log_lines
                                all_nc = resultado.get('no_controlados_nuevos', []) + resultado.get('no_controlados_avisados', [])
                                all_c = resultado.get('controlados_nuevos', []) + resultado.get('controlados_avisados', [])
                                
                                nc_parsed = parse_and_aggregate_log_lines(all_nc, dia)
                                c_parsed = parse_and_aggregate_log_lines(all_c, dia)
                                forced_data = {'nc_errors': nc_parsed, 'c_errors': c_parsed}
            
                            html_content, _, _ = construir_html_resumen(dia, app_name, app_key, forced_data=forced_data)
                            body = html_content
                            
                            standard_subject = _get_subject(app_key, dia)
                            if not subject or subject.startswith("Manual Notice:"):
                                subject = standard_subject
                                
                        except Exception as e:
                            logger.error(f"Error generating template: {e}")
                            return {'error': f"Failed to generate template: {str(e)}", 'status': 500}
                    
                    # Determine sender name
                    sender_name = None
                    if use_template:
                         from mailer.builder import _get_sender_name
                         if subject: 
                             sender_name = _get_sender_name(app_key, subject)
            
                    if not subject or not body:
                         return {'error': 'Subject or Body missing (and not generated)', 'status': 400}
                        
                    # Send Email
                    send_email(subject, body, recipients, sender_name=sender_name)
                    
                    return {'message': 'Notice sent successfully', 'recipients': recipients, 'status': 200}
                    
                except Exception as e:
                    logger.error(f"Error sending manual notice logic: {e}")
                    return {'error': str(e), 'status': 500}

        future = executor.submit(run_logic)
        
        # Heartbeat loop
        while not future.done():
            yield " "  # Keep-alive space
            time.sleep(1)
            
        # Retrieve result
        try:
            result = future.result()
            # If error status in dict, yield it
            yield json.dumps(result)
        except Exception as e:
            logger.error(f"Error in manual notice stream: {e}")
            yield json.dumps({'error': str(e)})

    return Response(stream_with_context(generate()), mimetype='application/json', headers={'X-Accel-Buffering': 'no'})
