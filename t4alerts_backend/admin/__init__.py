"""
Admin module for T4 Alerts
Handles user permission management and admin operations
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import routes to register them with the blueprint
from t4alerts_backend.admin import routes
