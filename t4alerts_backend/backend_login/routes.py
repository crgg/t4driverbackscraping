from flask import Blueprint, request, jsonify
from t4alerts_backend.backend_login.strategies import EmailPasswordStrategy
from t4alerts_backend.common.utils import logger

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Instantiate Strategy (Could be injected or selected dynamically)
        auth_strategy = EmailPasswordStrategy()
        
        token, error = auth_strategy.authenticate(data)

        if error:
            logger.warning(f"Login failed: {error}")
            return jsonify({"msg": error}), 401
        
        logger.info(f"User logged in successfully: {data.get('email')}")
        return jsonify(access_token=token), 200

    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({"msg": "Internal Server Error"}), 500
