from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from t4alerts_backend.common.decorators import permission_required
from db.error_history import get_error_history

error_history_bp = Blueprint('error_history', __name__)

@error_history_bp.route('/', methods=['GET'])
@jwt_required()
@permission_required('view_errors')
def get_history():
    """
    Get global error history.
    Params: limit (default 100), offset (default 0)
    """
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        errors = get_error_history(limit, offset)
        
        # Format timestamps for JSON
        for err in errors:
            if err['first_seen']:
                # Send ISO format so frontend can handle timezone conversion
                err['first_seen'] = err['first_seen'].isoformat()
                
        return jsonify(errors), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@error_history_bp.route('/scan', methods=['POST'])
@jwt_required()
@permission_required('view_errors')
def scan_all_apps():
    """
    Triggers scraping for ALL configured apps for a specific date.
    Body: { "date": "YYYY-MM-DD" } (optional, defaults to today)
    """
    try:
        from datetime import datetime
        from app.config import APPS_CONFIG
        from app.scrapper import procesar_aplicacion

        data = request.get_json() or {}
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            dia = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        results_summary = []
        total_errors_found = 0
        
        for app_key, config in APPS_CONFIG.items():
            try:
                # Reuse existing scraper logic
                # This function already handles DB insertion for history via side-effects
                res = procesar_aplicacion(app_key, date_str, dia)
                
                # Count critical errors (new + alerted are both attempted to be saved to history)
                count = len(res['no_controlados_nuevos']) + len(res['no_controlados_avisados'])
                total_errors_found += count
                
                results_summary.append({
                    "app": config['name'],
                    "status": "success",
                    "critical_errors": count
                })
            except Exception as e_app:
                results_summary.append({
                    "app": config.get('name', app_key),
                    "status": "error",
                    "error": str(e_app)
                })

        return jsonify({
            "message": "Global scan completed",
            "date": date_str,
            "total_critical_errors_processed": total_errors_found,
            "details": results_summary
        }), 200

    except Exception as e:
        return jsonify({"error": f"Global scan failed: {str(e)}"}), 500
