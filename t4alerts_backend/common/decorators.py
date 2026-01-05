"""
Custom decorators for authentication and authorization
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from t4alerts_backend.common.utils import logger


def admin_required(fn):
    """
    Decorator to require admin role for accessing a route
    Must be used after @jwt_required()
    
    Usage:
        @jwt_required()
        @admin_required
        def admin_only_route():
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            
            role = claims.get('role', 'user')
            
            if role != 'admin':
                logger.warning(f"Non-admin user attempted to access admin route: {fn.__name__}")
                return jsonify({"msg": "Admin access required"}), 403
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in admin_required decorator: {e}")
            return jsonify({"msg": "Authorization error"}), 500
    
    return wrapper


def permission_required(permission_name):
    """
    Decorator to require a specific permission for accessing a route
    Admins automatically have all permissions
    Must be used after @jwt_required()
    
    Args:
        permission_name (str): The required permission (e.g., 'view_certificates')
    
    Usage:
        @jwt_required()
        @permission_required('view_certificates')
        def certificates_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                
                # Admin users have all permissions
                role = claims.get('role', 'user')
                if role == 'admin':
                    return fn(*args, **kwargs)
                
                # Check if user has the required permission
                user_id = claims.get('sub')  # 'sub' is the standard JWT claim for user identity
                permissions = claims.get('permissions', [])
                
                if permission_name not in permissions:
                    logger.warning(f"User {user_id} attempted to access {fn.__name__} without {permission_name} permission")
                    return jsonify({"msg": f"Permission denied. Required: {permission_name}"}), 403
                
                return fn(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in permission_required decorator: {e}")
                return jsonify({"msg": "Authorization error"}), 500
        
        return wrapper
    return decorator
