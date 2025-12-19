from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from db.connection import get_cursor
import logging

dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

@dashboard_bp.route('/errors', methods=['GET'])
@jwt_required()
def get_error_stats():
    """
    Returns statistics for the errors dashboard.
    Data is queried directly from the 'postgres' database (scraping DB).
    """
    stats = {
        "errors_by_app": [],
        "errors_by_type": [],
        "recent_errors": []
    }
    
    try:
        with get_cursor() as cur:
            # 1. Bar Chart: Errors per App (Uncontrolled)
            cur.execute("""
                SELECT app_key, COUNT(*) 
                FROM alerted_errors 
                WHERE tipo = 'no_controlado' 
                GROUP BY app_key 
                ORDER BY COUNT(*) DESC
            """)
            rows = cur.fetchall()
            stats["errors_by_app"] = [{"label": r[0], "value": r[1]} for r in rows]
            
            # 2. Donut Chart: Distribution of Error Types (Controlado vs No Controlado)
            cur.execute("""
                SELECT tipo, COUNT(*) 
                FROM alerted_errors 
                GROUP BY tipo
            """)
            rows = cur.fetchall()
            stats["errors_by_type"] = [{"label": r[0], "value": r[1]} for r in rows]
            
            # 3. Notifications/Direct Feed: Recent Errors with Recurrence
            # Shows 'no_controlado' errors, grouping by signature to show recurrence count
            cur.execute("""
                SELECT 
                    app_key, 
                    signature, 
                    MAX(first_seen_at) as last_seen, 
                    COUNT(*) as recurrence 
                FROM alerted_errors 
                WHERE tipo = 'no_controlado'
                GROUP BY app_key, signature 
                ORDER BY last_seen DESC 
                LIMIT 20
            """)
            rows = cur.fetchall()
            stats["recent_errors"] = [{
                "app": r[0], 
                "signature": r[1], 
                "timestamp": r[2].isoformat() if r[2] else None, 
                "recurrence": r[3]
            } for r in rows]
            
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({"error": "Failed to fetch dashboard statistics"}), 500
