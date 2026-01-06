"""
Apps Manager Blueprint - Initialize module
"""
from flask import Blueprint

apps_manager_bp = Blueprint('apps_manager', __name__)

from . import routes
