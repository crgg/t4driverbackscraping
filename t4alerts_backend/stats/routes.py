from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.config import APPS_CONFIG
from db.connection import get_cursor
import logging
from datetime import datetime

stats_bp = Blueprint('stats', __name__)
logger = logging.getLogger(__name__)

@stats_bp.route('/apps', methods=['GET'])
@jwt_required()
def get_apps():
    """
    Returns the list of configured applications for the accordion menu.
    """
    try:
        apps_list = []
        for key, config in APPS_CONFIG.items():
            apps_list.append({
                "key": key,
                "name": config.get("name", key)
            })
        logger.info(f"Returning {len(apps_list)} apps")
        return jsonify(apps_list), 200
    except Exception as e:
        logger.error(f"Error fetching apps list: {e}")
        return jsonify({"error": str(e)}), 500

# Debug endpoint (no auth) for testing
@stats_bp.route('/debug/apps', methods=['GET'])
def debug_apps():
    """Debug endpoint without JWT to verify config is loaded."""
    try:
        apps_list = []
        for key, config in APPS_CONFIG.items():
            apps_list.append({
                "key": key,
                "name": config.get("name", key)
            })
        return jsonify({"status": "ok", "count": len(apps_list), "apps": apps_list}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@stats_bp.route('/view/<app_key>', methods=['GET'])
@jwt_required()
def get_app_stats(app_key):
    """
    Returns logs and statistics for a specific app and date.
    Query Params: ?date=YYYY-MM-DD (default: today)
    """
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    response_data = {
        "logs": {
            "uncontrolled": [],
            "controlled": []
        },
        "stats": {
            "sql_errors": 0,
            "non_sql_errors": 0
        }
    }

    try:
        if app_key not in APPS_CONFIG:
            return jsonify({"error": "App not found"}), 404

        with get_cursor() as cur:
            # Fetch errors for the specific date and app
            # Note: casting first_seen_at to date to filter
            query = """
                SELECT 
                    tipo, 
                    signature, 
                    first_seen_at, 
                    created_at 
                FROM alerted_errors 
                WHERE app_key = %s 
                AND DATE(first_seen_at) = %s
                ORDER BY first_seen_at DESC
            """
            cur.execute(query, (app_key, date_str))
            rows = cur.fetchall()

            # Process rows
            uncontrolled_logs = []
            controlled_logs = []
            sql_count = 0
            non_sql_count = 0

            # Temporary frequency map for this view (or we can just list them all)
            # The user asked for "xN" recurrence. 
            # If we are listing individual rows, recurrence might be 1 unless we aggregate.
            # The PRD example showed: "2025-12-19 ... message ... (x1)"
            # Since the table alerted_errors stores one row per error occurrence (usually),
            # or creates a new row. Wait, scraper logic usually inserts every time or updates?
            # Let's assume we group by signature for the view to calculate (xN).
            
            # Let's do aggregation in python for flexibility or SQL.
            # Grouping by signature + time slice might be complex if we want chronological order.
            # User example: "Message (x1)". 
            # Let's just aggregate by signature for the "stats" charts, 
            # but for "Logs" view, usually users want to see the sequence.
            # HOWEVER, the User example explicitly shows `(x1)` at the end.
            # I will group by signature + approximate time or just group by signature entirely for the day?
            # "2025-12-19 09:39:10 ... Message ... (x1)" implies a timestamp.
            # If it happened 5 times, showing one timestamp is ambiguous unless it's "Last Seen".
            # Let's group by signature and show MAX(timestamp) and Count.

            # Re-querying with Group By to match the requested format
            group_query = """
                SELECT 
                    tipo,
                    signature,
                    MAX(first_seen_at) as last_seen,
                    COUNT(*) as count
                FROM alerted_errors
                WHERE app_key = %s
                AND DATE(first_seen_at) = %s
                GROUP BY tipo, signature
                ORDER BY last_seen DESC
            """
            
            cur.execute(group_query, (app_key, date_str))
            grouped_rows = cur.fetchall()

            for row in grouped_rows:
                tipo, signature, last_seen, count = row
                
                # Format: YYYY-MM-DD HH:MM:SS — Message (xN)
                formatted_log = {
                    "timestamp": last_seen.strftime('%Y-%m-%d %H:%M:%S') if last_seen else "N/A",
                    "message": signature,
                    "count": count,
                    "full_text": f"{last_seen.strftime('%Y-%m-%d %H:%M:%S')} — {signature} (x{count})"
                }

                if tipo == 'no_controlado':
                    uncontrolled_logs.append(formatted_log)
                    
                    # Check for SQL error keywords
                    # Simple heuristic: "SQLSTATE", "SQL", "DB2", "ORA-", "Postgres"
                    sig_upper = signature.upper()
                    if "SQL" in sig_upper or "DB2" in sig_upper or "ORA-" in sig_upper or "CONSTRAINT" in sig_upper:
                        sql_count += count
                    else:
                        non_sql_count += count
                        
                elif tipo == 'controlado':
                    controlled_logs.append(formatted_log)
                    # Controlled errors usually not counted in SQL/Non-SQL stats chart unless specified.
                    # User said: "grafico de distribucion de errores SQL y otro de errores NO sql"
                    # typically refers to the crash/uncontrolled ones. I'll stick to that for now.

            response_data["logs"]["uncontrolled"] = uncontrolled_logs
            response_data["logs"]["controlled"] = controlled_logs
            response_data["stats"]["sql_errors"] = sql_count
            response_data["stats"]["non_sql_errors"] = non_sql_count
            
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching stats for {app_key}: {e}")
        return jsonify({"error": "Failed to fetch app stats"}), 500
