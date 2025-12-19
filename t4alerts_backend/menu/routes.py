from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/', methods=['GET'])
@jwt_required()
def get_menu_options():
    """
    Returns available menu options. 
    Frontend can use this to verify session and get feature flags if any.
    """
    return jsonify({
        "options": [
            {
                "id": "certificates",
                "label": "SSL Certificates",
                "route": "/certificates",
                "icon": "ssl_icon" 
            },
            {
                "id": "errors",
                "label": "Error Dashboard",
                "route": "/errors",
                "icon": "error_icon"
            }
        ]
    }), 200
