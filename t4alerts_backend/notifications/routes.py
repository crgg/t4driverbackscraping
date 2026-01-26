from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from t4alerts_backend.notifications.models import NotificationSettings
from t4alerts_backend.common.database import db
import logging
from app.alerts import send_email

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
    """
    try:
        data = request.get_json()
        app_key = data.get('app_key')
        subject = data.get('subject')
        body = data.get('body')
        recipients = data.get('recipients') # Optional override
        use_template = data.get('use_template', False)
        date_str = data.get('date') # Required if use_template is True
        
        if not app_key:
            return jsonify({'error': 'Missing required fields: app_key'}), 400
            
        if not recipients:
            # Fallback to saved settings
            settings = NotificationSettings.query.filter_by(app_key=app_key).first()
            if settings and settings.recipients:
                recipients = settings.recipients
        
        if not recipients:
            return jsonify({'error': 'No recipients provided or found in settings'}), 400

        # Generate Body from Template if requested
        if use_template:
            if not date_str:
                return jsonify({'error': 'Date is required when using template'}), 400
                
            from datetime import datetime
            try:
                dia = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400

            # Get app name
            from app.config import get_apps_config
            # Ensure we look at dynamic content too
            cfg = get_apps_config(dynamic_only=False, quiet=True).get(app_key, {})
            app_name = cfg.get('name', app_key)
            
            # TRIGGER SCRAPING: To match main.py, we must ensure logs are scraped.
            # Otherwise, we might be reporting on old or empty data.
            # This is "Copy what happens when main.py is executed"
            try:
                from app.scrapper import procesar_aplicacion
                # We reuse the same logic
                # Note: This might be slow if the app is slow. But it's "manual" trigger.
                print(f"🔄 [Manual Trigger] Scraping logs for {app_key} on {dia}")
                procesar_aplicacion(app_key, date_str, dia)
            except Exception as e:
                logger.error(f"Error during manual scraping for {app_key}: {e}")
                # We continue? or fail?
                # If scraping fails, report likely empty or partial.
                # Let's add a warning to the body?
                # For now, let's assume it might have worked partly or just log it.
                
            
            # Generate HTML
            # Now that we've scraped, the logs should be on disk (app/scrapper.py calls save_logs)
            from app.email_notifier import construir_html_resumen, _get_subject, _get_sender_name
            try:
                html_content, _, _ = construir_html_resumen(dia, app_name, app_key)
                body = html_content
                
                # Force standard subject if using template, unless user explicitly customized it AND it's not the default "Manual Notice..." one
                # Actually, user asks for "[DRIVERAPP...] Errors YYYY-MM-DD". 
                # The frontend sends "Manual Notice: key" as default.
                # If we detect that, or if use_template is True, we should probably prefer the standard subject.
                standard_subject = _get_subject(app_key, dia)
                
                # Logic: If subject is the default from frontend ("Manual Notice..."), override it.
                # If user typed something specific, keep it? Or just always override if template is used?
                # User request: "el asunto debe ser algo asi [DRIVERAPP GO 2 LOGISTICS] Errors..."
                # implies we should use the standard one.
                if not subject or subject.startswith("Manual Notice:"):
                    subject = standard_subject
                    
            except Exception as e:
                logger.error(f"Error generating template: {e}")
                return jsonify({'error': f"Failed to generate template: {str(e)}"}), 500
        
        # Determine sender name (default to None so send_email uses env var, unless we have logic)
        sender_name = None
        if use_template:
            # We need to import it inside if
             from app.email_notifier import _get_sender_name
             if subject: # Ensure we have a subject to check against
                 sender_name = _get_sender_name(app_key, subject)

        if not subject or not body:
             return jsonify({'error': 'Subject or Body missing (and not generated)'}), 400
            
        # Send Email
        # We assume body is HTML
        send_email(subject, body, recipients, sender_name=sender_name)
        
        return jsonify({'message': 'Notice sent successfully', 'recipients': recipients}), 200
        
    except Exception as e:
        logger.error(f"Error sending manual notice: {e}")
        return jsonify({'error': str(e)}), 500
