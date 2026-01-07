"""
REST API routes for app management.
Provides CRUD endpoints for monitored applications.
"""
from flask import jsonify, request
from flask_jwt_extended import jwt_required
from t4alerts_backend.common.decorators import admin_required
from t4alerts_backend.common.utils import logger
from . import apps_manager_bp
from .services import AppManagerService


# COMENTADO POR SOLICITUD DE USUARIO - La gestión de apps ahora se hace vía Custom Scan
# NOTA: Descomentar para habilitar el API si Custom Scan necesita guardar cambios.

# @apps_manager_bp.route('/', methods=['GET'])
# @jwt_required()
# def list_apps():
#     """
#     List all monitored applications.
#     Returns apps without plaintext passwords for security.
#     """
#     try:
#         apps = AppManagerService.list_apps()
#         logger.info(f"Listing {len(apps)} apps")
#         return jsonify(apps), 200
#     except Exception as e:
#         logger.error(f"Error listing apps: {e}")
#         return jsonify({"error": str(e)}), 500
# 
# 
# @apps_manager_bp.route('/<int:app_id>', methods=['GET'])
# @jwt_required()
# def get_app(app_id):
#     """
#     Get a single app by ID.
#     """
#     try:
#         app = AppManagerService.get_app(app_id, include_credentials=False)
#         
#         if not app:
#             return jsonify({"error": "App not found"}), 404
#         
#         return jsonify(app), 200
#     except Exception as e:
#         logger.error(f"Error getting app {app_id}: {e}")
#         return jsonify({"error": str(e)}), 500
# 
# 
@apps_manager_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def create_app():
    """
    Create a new monitored application.
    Requires admin privileges.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        app = AppManagerService.create_app(data)
        logger.info(f"App created: {app['app_key']}")
        
        return jsonify(app), 201
        
    except ValueError as e:
        logger.warning(f"Validation error creating app: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating app: {e}")
        return jsonify({"error": str(e)}), 500
# 
# 
# @apps_manager_bp.route('/<int:app_id>', methods=['PUT'])
# @jwt_required()
# @admin_required
# def update_app(app_id):
#     """
#     Update an existing app.
#     """
#     try:
#         data = request.get_json()
#         
#         if not data:
#             return jsonify({"error": "No data provided"}), 400
#         
#         app = AppManagerService.update_app(app_id, data)
#         logger.info(f"App updated: {app['app_key']}")
#         
#         return jsonify(app), 200
#         
#     except ValueError as e:
#         logger.warning(f"Validation error updating app: {e}")
#         return jsonify({"error": str(e)}), 400
#     except Exception as e:
#         logger.error(f"Error updating app: {e}")
#         return jsonify({"error": str(e)}), 500
# 
# 
# @apps_manager_bp.route('/<int:app_id>', methods=['DELETE'])
# @jwt_required()
# @admin_required
# def delete_app(app_id):
#     """
#     Delete an app.
#     """
#     try:
#         AppManagerService.delete_app(app_id)
#         logger.info(f"App deleted: {app_id}")
#         
#         return jsonify({"message": "App deleted successfully"}), 200
#         
#     except ValueError as e:
#         logger.warning(f"App not found for deletion: {app_id}")
#         return jsonify({"error": str(e)}), 404
#     except Exception as e:
#         logger.error(f"Error deleting app: {e}")
#         return jsonify({"error": str(e)}), 500
# 
# 
# @apps_manager_bp.route('/<int:app_id>/scan', methods=['POST'])
# @jwt_required()
# @admin_required
# def scan_app(app_id):
#     """
#     Trigger on-demand scraping for a specific app.
#     """
#     try:
#         data = request.get_json() or {}
#         date_str = data.get('date')
#         
#         result = AppManagerService.scan_app(app_id, date_str)
#         logger.info(f"Scan triggered for app {app_id}")
#         
#         return jsonify(result), 200
#         
#     except ValueError as e:
#         logger.warning(f"Validation error scanning app: {e}")
#         return jsonify({"error": str(e)}), 400
#     except Exception as e:
#         logger.error(f"Error scanning app: {e}")
#         return jsonify({"error": str(e)}), 500
# 
# 
# @apps_manager_bp.route('/export-config', methods=['GET'])
# @jwt_required()
# @admin_required
# def export_config():
#     """
#     Export all active apps in APPS_CONFIG format.
#     """
#     try:
#         config = AppManagerService.export_to_legacy_format()
#         logger.info("Config exported successfully")
#         
#         return jsonify(config), 200
#         
#     except Exception as e:
#         logger.error(f"Error exporting config: {e}")
#         return jsonify({"error": str(e)}), 500
