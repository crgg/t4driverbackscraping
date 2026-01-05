"""
Permission models for the admin module
"""
from datetime import datetime
from t4alerts_backend.common.database import db
from t4alerts_backend.common.utils import logger


class UserPermission(db.Model):
    """
    Model representing granular permissions for users
    Valid permission names: 'view_certificates', 'view_errors'
    """
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    permission_name = db.Column(db.String(50), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'permission_name', name='unique_user_permission'),
    )
    
    def __repr__(self):
        return f'<UserPermission user_id={self.user_id} permission={self.permission_name}>'
    
    @staticmethod
    def has_permission(user_id, permission_name):
        """
        Check if a user has a specific permission
        
        Args:
            user_id (int): The user ID to check
            permission_name (str): The permission to check for
            
        Returns:
            bool: True if user has the permission, False otherwise
        """
        try:
            permission = UserPermission.query.filter_by(
                user_id=user_id,
                permission_name=permission_name
            ).first()
            return permission is not None
        except Exception as e:
            logger.error(f"Error checking permission for user {user_id}: {e}")
            return False
    
    @staticmethod
    def grant_permission(user_id, permission_name, granted_by_user_id=None):
        """
        Grant a permission to a user
        
        Args:
            user_id (int): The user ID to grant permission to
            permission_name (str): The permission to grant
            granted_by_user_id (int, optional): The admin user ID granting the permission
            
        Returns:
            tuple: (UserPermission object or None, error message or None)
        """
        try:
            # Check if permission already exists
            existing = UserPermission.query.filter_by(
                user_id=user_id,
                permission_name=permission_name
            ).first()
            
            if existing:
                logger.info(f"Permission {permission_name} already granted to user {user_id}")
                return existing, None
            
            # Create new permission
            new_permission = UserPermission(
                user_id=user_id,
                permission_name=permission_name,
                granted_by=granted_by_user_id
            )
            
            db.session.add(new_permission)
            db.session.commit()
            
            logger.info(f"✅ Granted permission '{permission_name}' to user {user_id} by admin {granted_by_user_id}")
            return new_permission, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error granting permission to user {user_id}: {e}")
            return None, str(e)
    
    @staticmethod
    def revoke_permission(user_id, permission_name):
        """
        Revoke a permission from a user
        
        Args:
            user_id (int): The user ID to revoke permission from
            permission_name (str): The permission to revoke
            
        Returns:
            tuple: (bool success, error message or None)
        """
        try:
            permission = UserPermission.query.filter_by(
                user_id=user_id,
                permission_name=permission_name
            ).first()
            
            if not permission:
                logger.warning(f"Attempted to revoke non-existent permission {permission_name} from user {user_id}")
                return True, None  # Not an error, permission doesn't exist
            
            db.session.delete(permission)
            db.session.commit()
            
            logger.info(f"🚫 Revoked permission '{permission_name}' from user {user_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error revoking permission from user {user_id}: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_permissions(user_id):
        """
        Get all permissions for a specific user
        
        Args:
            user_id (int): The user ID
            
        Returns:
            list: List of permission names
        """
        try:
            permissions = UserPermission.query.filter_by(user_id=user_id).all()
            return [p.permission_name for p in permissions]
        except Exception as e:
            logger.error(f"Error fetching permissions for user {user_id}: {e}")
            return []
