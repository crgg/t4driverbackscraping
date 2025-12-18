import sys
import os

# Add the parent directory to sys.path to allow absolute imports to work
# even when running this script directly from the subdirectory.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    CORS(app) # Enable CORS for all domains

    # Register Blueprints
    app.register_blueprint(registration_bp, url_prefix='/api/auth')
    app.register_blueprint(login_bp, url_prefix='/api/auth')

    # Create Tables within Context
    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
