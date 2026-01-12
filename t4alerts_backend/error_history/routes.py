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
# REMOVED: Endpoint '/scan' eliminado
# 
# Razón: Cada vez que se hace scraping (desde custom-scan o desde errors/[app]),
# procesar_aplicacion() ya guarda automáticamente los errores en error_history.
# No es necesario un endpoint que haga scraping masivo de todas las apps.
