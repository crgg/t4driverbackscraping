"""
Admin routes for user and permission management
All routes require admin role
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import admin_bp
from t4alerts_backend.admin.services import PermissionService
from t4alerts_backend.common.decorators import admin_required
from t4alerts_backend.common.utils import logger


@admin_bp.route('/users', methods=['GET', 'POST'])
@jwt_required()
@admin_required
def users():
    """
    GET: Get all users with their permissions
    POST: Create a new user
    
    POST Request body:
        {
            "email": "user@example.com",
            "password": "password123",
            "role": "user"  // optional, defaults to "user"
        }
    
    Returns:
        GET: JSON response with list of users
        POST: JSON response with created user details
    """
    if request.method == 'GET':
        return list_users()
    elif request.method == 'POST':
        return create_user()


def list_users():
    """
    Get all users with their permissions
    
    Returns:
        JSON response with list of users
    """
    try:
        users, error = PermissionService.list_all_users()
        
        if error:
            logger.error(f"Error listing users: {error}")
            return jsonify({"msg": "Failed to retrieve users", "error": error}), 500
        
        return jsonify({
            "users": users,
            "total": len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in list_users: {e}")
        return jsonify({"msg": "Internal server error"}), 500


def create_user():
    """
    Create a new user
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password123",
            "role": "user"  // optional, defaults to "user"
        }
    
    Returns:
        JSON response with created user details
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"msg": "Missing request body"}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user').strip().lower()
        
        if not email:
            return jsonify({"msg": "Email is required"}), 400
        
        if not password:
            return jsonify({"msg": "Password is required"}), 400
        
        # Get the admin user ID making this change
        admin_user_id = get_jwt_identity()
        
        # Create user
        user_data, error = PermissionService.create_user(
            email=email,
            password=password,
            role=role,
            admin_user_id=admin_user_id
        )
        
        if error:
            return jsonify({"msg": "Failed to create user", "error": error}), 400
        
        return jsonify({
            "msg": "User created successfully",
            "user": user_data
        }), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in create_user: {e}")
        return jsonify({"msg": "Internal server error"}), 500
    """
    Get all users with their permissions
    
    Returns:
        JSON response with list of users
    """
    try:
        users, error = PermissionService.list_all_users()
        
        if error:
            logger.error(f"Error listing users: {error}")
            return jsonify({"msg": "Failed to retrieve users", "error": error}), 500
        
        return jsonify({
            "users": users,
            "total": len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in list_users: {e}")
        return jsonify({"msg": "Internal server error"}), 500


@admin_bp.route('/users/<int:user_id>/permissions', methods=['PUT'])
@jwt_required()
@admin_required
def update_permissions(user_id):
    """
    Update permissions for a specific user
    
    Request body:
        {
            "permissions": ["view_certificates", "view_errors"]
        }
    
    Args:
        user_id (int): The user ID to update
        
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        if not data or 'permissions' not in data:
            return jsonify({"msg": "Missing 'permissions' field in request"}), 400
        
        permissions = data.get('permissions', [])
        
        # Validate that permissions is a list
        if not isinstance(permissions, list):
            return jsonify({"msg": "'permissions' must be an array"}), 400
        
        # Get the admin user ID making this change
        admin_user_id = get_jwt_identity()
        
        # Update permissions
        success, error = PermissionService.update_user_permissions(
            user_id=user_id,
            permissions_to_grant=permissions,
            admin_user_id=admin_user_id
        )
        
        if not success:
            return jsonify({"msg": "Failed to update permissions", "error": error}), 400
        
        # Get updated user details
        user_details, _ = PermissionService.get_user_details(user_id)
        
        return jsonify({
            "msg": "Permissions updated successfully",
            "user": user_details
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in update_permissions: {e}")
        return jsonify({"msg": "Internal server error"}), 500


@admin_bp.route('/permissions/available', methods=['GET'])
@jwt_required()
@admin_required
def get_available_permissions():
    """
    Get list of all available permission types
    
    Returns:
        JSON response with available permissions
    """
    try:
        permissions = PermissionService.get_available_permissions()
        
        return jsonify({
            "permissions": permissions,
            "descriptions": {
                "view_certificates": "Access to SSL Certificates section",
                "view_errors": "Access to Error Dashboard section"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available permissions: {e}")
        return jsonify({"msg": "Internal server error"}), 500


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_details(user_id):
    """
    Get detailed information about a specific user
    
    Args:
        user_id (int): The user ID
        
    Returns:
        JSON response with user details
    """
    try:
        user_details, error = PermissionService.get_user_details(user_id)
        
        if error:
            return jsonify({"msg": error}), 404 if "not found" in error.lower() else 500
        
        return jsonify(user_details), 200
        
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return jsonify({"msg": "Internal server error"}), 500


@admin_bp.route('/users/<int:user_id>/password', methods=['PUT'])
@jwt_required()
@admin_required
def change_user_password(user_id):
    """
    Change password for a specific user
    
    Request body:
        {
            "password": "new_password_here"
        }
    
    Args:
        user_id (int): The user ID to update
        
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({"msg": "Missing 'password' field in request"}), 400
        
        new_password = data.get('password', '').strip()
        
        if not new_password:
            return jsonify({"msg": "Password cannot be empty"}), 400
        
        # Get the admin user ID making this change
        admin_user_id = get_jwt_identity()
        
        # Change password
        success, error = PermissionService.change_user_password(
            user_id=user_id,
            new_password=new_password,
            admin_user_id=admin_user_id
        )
        
        if not success:
            return jsonify({"msg": "Failed to change password", "error": error}), 400
        
        return jsonify({
            "msg": "Password changed successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in change_user_password: {e}")
        return jsonify({"msg": "Internal server error"}), 500
