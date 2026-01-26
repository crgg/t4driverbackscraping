import sys
import os

# Add the project root to sys.path to find core modules (app, db, etc.)
# If running from /Users/administrator/Desktop/scrapping_project/t4alerts_backend/app.py
# then 1st dirname is t4alerts_backend, 2nd dirname is project root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from dotenv import load_dotenv
# Load environment variables from the root .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from t4alerts_backend.config import Config
from t4alerts_backend.common.database import db
from t4alerts_backend.backend_registration import registration_bp
from t4alerts_backend.backend_login import login_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # DEBUG: Print JWT Config
    print(f"🔧 JWT_SECRET_KEY: {app.config.get('JWT_SECRET_KEY')}")
    print(f"🔧 JWT_TOKEN_LOCATION: {app.config.get('JWT_TOKEN_LOCATION')}")
    print(f"🔧 JWT_COOKIE_CSRF_PROTECT: {app.config.get('JWT_COOKIE_CSRF_PROTECT')}")


    # Initialize Extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Custom JWT Error Handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return {"msg": f"Invalid token: {error_string}", "error": "invalid_token"}, 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"msg": "Token has expired", "error": "token_expired"}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return {"msg": f"Missing Authorization Header: {error_string}", "error": "authorization_header_missing"}, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {"msg": "Token has been revoked", "error": "token_revoked"}, 401

    # CORS Configuration
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Blueprints
    # Register Blueprints
    app.register_blueprint(registration_bp, url_prefix='/api/auth')
    app.register_blueprint(login_bp, url_prefix='/api/auth')
    
    # New V2.0 Blueprints
    from t4alerts_backend.menu import menu_bp
    from t4alerts_backend.certificates import certificates_bp
    from t4alerts_backend.dashboard import dashboard_bp
    from t4alerts_backend.admin import admin_bp
    from t4alerts_backend.apps_manager import apps_manager_bp
    
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(certificates_bp, url_prefix='/api/certificates')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(apps_manager_bp, url_prefix='/api/apps')
    
    from t4alerts_backend.stats import stats_bp
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    
    # Notifications Blueprint
    from t4alerts_backend.notifications.routes import notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    # Error History Blueprint (PRD 2.0)
    from t4alerts_backend.error_history.routes import error_history_bp
    app.register_blueprint(error_history_bp, url_prefix='/api/error-history')

    # Create Tables within Context
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from t4alerts_backend.admin.models import UserPermission
        from t4alerts_backend.apps_manager.models import MonitoredApp
        from t4alerts_backend.certificates.models import SSLCertificate
        from t4alerts_backend.notifications.models import NotificationSettings
        
        db.create_all()
        
        # Initialize alerted_errors table for scraping system
        # This ensures the table exists after docker-compose down -v
        try:
            from db import init_db
            init_db()
            print("✅ Database initialized: alerted_errors table ready")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize alerted_errors table: {e}")
            print("   The stats endpoint may fall back to reading .log files")
        
        # Initialize error_history table for Error History view
        try:
            from db.error_history import init_error_history_db
            init_error_history_db()
            print("✅ Database initialized: error_history table ready")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize error_history table: {e}")
        
        # Log that permissions system is ready
        print("✅ Permissions system initialized")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
