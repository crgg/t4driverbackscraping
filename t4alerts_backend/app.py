import sys
import os

# Add the parent directory to sys.path to allow absolute imports to work
# even when running this script directly from the subdirectory.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Load environment variables from the root .env file
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, '.env'))

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

    # Initialize Extensions
    db.init_app(app)
    jwt = JWTManager(app)
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
    
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(certificates_bp, url_prefix='/api/certificates')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    from t4alerts_backend.stats import stats_bp
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    
    # Error History Blueprint (PRD 2.0)
    from t4alerts_backend.error_history.routes import error_history_bp
    app.register_blueprint(error_history_bp, url_prefix='/api/error-history')

    # Create Tables within Context
    with app.app_context():
        # Import admin models to register them with SQLAlchemy
        from t4alerts_backend.admin.models import UserPermission
        
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
        
        # Log that permissions system is ready
        print("✅ Permissions system initialized")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
