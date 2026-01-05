"""
Business logic services for admin operations
"""
from t4alerts_backend.common.models import User
from t4alerts_backend.admin.models import UserPermission
from t4alerts_backend.common.utils import logger


class PermissionService:
    """
    Service class for managing user permissions
    Provides high-level business logic for admin operations
    """
    
    AVAILABLE_PERMISSIONS = ['view_certificates', 'view_errors']
    
    @staticmethod
    def get_available_permissions():
        """
        Get list of all available permission types
        
        Returns:
            list: Available permission names
        """
        return PermissionService.AVAILABLE_PERMISSIONS.copy()
    
    @staticmethod
    def list_all_users():
        """
        Get all users with their current permissions
        
        Returns:
            tuple: (list of user dicts, error message or None)
        """
        try:
            users = User.query.all()
            
            user_list = []
            for user in users:
                permissions = UserPermission.get_user_permissions(user.id)
                
                user_list.append({
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'permissions': permissions,
                    'has_certificates_access': 'view_certificates' in permissions,
                    'has_errors_access': 'view_errors' in permissions
                })
            
            logger.info(f"Retrieved {len(user_list)} users for admin panel")
            return user_list, None
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return None, str(e)
    
    @staticmethod
    def update_user_permissions(user_id, permissions_to_grant, admin_user_id=None):
        """
        Update a user's permissions (grant/revoke as needed)
        
        Args:
            user_id (int): The user ID to update
            permissions_to_grant (list): List of permission names to grant
            admin_user_id (int, optional): The admin making the change
            
        Returns:
            tuple: (success bool, error message or None)
        """
        try:
            # Validate user exists
            user = User.query.get(user_id)
            if not user:
                logger.warning(f"Attempted to update permissions for non-existent user {user_id}")
                return False, "User not found"
            
            # Validate permissions
            for perm in permissions_to_grant:
                if perm not in PermissionService.AVAILABLE_PERMISSIONS:
                    logger.warning(f"Invalid permission name: {perm}")
                    return False, f"Invalid permission: {perm}"
            
            # Get current permissions
            current_permissions = UserPermission.get_user_permissions(user_id)
            
            # Determine what to grant and what to revoke
            to_grant = set(permissions_to_grant) - set(current_permissions)
            to_revoke = set(current_permissions) - set(permissions_to_grant)
            
            # Grant new permissions
            for perm in to_grant:
                _, error = UserPermission.grant_permission(user_id, perm, admin_user_id)
                if error:
                    logger.error(f"Failed to grant {perm} to user {user_id}: {error}")
                    return False, error
            
            # Revoke removed permissions
            for perm in to_revoke:
                success, error = UserPermission.revoke_permission(user_id, perm)
                if not success:
                    logger.error(f"Failed to revoke {perm} from user {user_id}: {error}")
                    return False, error
            
            logger.info(f"✅ Updated permissions for user {user.email} (ID: {user_id}) - Granted: {list(to_grant)}, Revoked: {list(to_revoke)}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error updating permissions for user {user_id}: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_details(user_id):
        """
        Get detailed information about a specific user
        
        Args:
            user_id (int): The user ID
            
        Returns:
            tuple: (user dict or None, error message or None)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            permissions = UserPermission.get_user_permissions(user.id)
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'permissions': permissions,
                'is_admin': user.is_admin()
            }
            
            return user_data, None
            
        except Exception as e:
            logger.error(f"Error fetching user details for {user_id}: {e}")
            return None, str(e)
