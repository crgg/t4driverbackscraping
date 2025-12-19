from flask import Blueprint, jsonify

# Include routes to ensure they are registered with the blueprint
from .routes import certificates_bp
