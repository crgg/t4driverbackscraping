from flask import Blueprint, request, jsonify
from t4alerts_backend.backend_registration.factory import UserFactory
from t4alerts_backend.common.database import db
from t4alerts_backend.common.models import User
from t4alerts_backend.common.utils import logger
import sys
import os
# Add parent directory to path to access app.alerts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.alerts import send_email # Import from parent project

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/register', methods=['POST'])
def register():
    """
    Public registration is disabled for security.
    Users must be created via CLI scripts (create_user.py or create_admin_user.py).
    """
    logger.warning("Attempted access to disabled registration endpoint")
    return jsonify({
        "error": "Public registration is disabled",
        "message": "User accounts must be created by administrators. Please contact your system administrator."
    }), 403

# ORIGINAL REGISTRATION CODE (DISABLED)
# Kept for reference - can be re-enabled if needed
"""
@registration_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user') # Default to user

        if not email or not password:
            return jsonify({"msg": "Missing email or password"}), 400

        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({"msg": "User already exists"}), 400

        # Use Factory to create user
        new_user = UserFactory.create_user(email, password, role)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {email} as {role}")

        # --- Email Notification Logic ---
        try:
            subject = "Welcome to T4 Alerts 🚨"
            body = (
                f"<h2>Welcome to T4 Alerts!</h2>"
                f"<p>Hello,</p>"
                f"<p>Your registration for the email <b>{email}</b> was successful.</p>"
                f"<p>You can now login to the platform.</p>"
                f"<br><p>Best regards,<br><b>T4Alerts Team</b></p>"
            )
            send_email(subject, body, [email], sender_name="t4alerts")
            logger.info(f"Confirmation email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

        return jsonify({"msg": "User created successfully"}), 201

    except Exception as e:
        logger.error(f"Error in registration: {e}")
        return jsonify({"msg": "Internal Server Error"}), 500
"""
