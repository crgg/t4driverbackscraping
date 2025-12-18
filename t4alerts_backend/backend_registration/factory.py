from t4alerts_backend.common.models import User
from t4alerts_backend.common.utils import hash_password

class UserFactory:
    """
    Factory Class to create User instances based on role.
    """
    @staticmethod
    def create_user(email, password, role="user"):
        hashed_pw = hash_password(password)
        
        # In a more complex factory, specific classes (AdminUser, StandardUser)
        # could be instantiated if they inherited from User or if User was polymorphic.
        # For this Flask-SQLAlchemy setup, we configure the single User model differently.
        
        if role == "admin":
            return User(email=email, password_hash=hashed_pw, role="admin")
        elif role == "user":
            return User(email=email, password_hash=hashed_pw, role="user")
        else:
            raise ValueError(f"Invalid role provided: {role}")
