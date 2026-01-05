from datetime import datetime
from t4alerts_backend.common.database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with permissions
    # Must specify foreign_keys because UserPermission has TWO foreign keys to User
    # (user_id and granted_by). We want to use user_id for this relationship.
    permissions = db.relationship(
        'UserPermission',
        foreign_keys='UserPermission.user_id',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<User {self.email}>'

    def is_admin(self):
        return self.role == 'admin'
    
    def get_permissions(self):
        """
        Get list of permission names for this user
        
        Returns:
            list: List of permission strings (e.g., ['view_certificates'])
        """
        return [p.permission_name for p in self.permissions]

