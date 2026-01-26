from abc import ABC, abstractmethod
from flask_jwt_extended import create_access_token
from t4alerts_backend.common.models import User
from t4alerts_backend.common.utils import check_password

class AuthStrategy(ABC):
    @abstractmethod
    def authenticate(self, credentials):
        pass

class EmailPasswordStrategy(AuthStrategy):
    """
    Concrete Strategy for Email/Password Authentication.
    """
    def authenticate(self, credentials):
        email = credentials.get('email')
        password = credentials.get('password')

        if not email or not password:
            return None, "Missing credentials"

        user = User.query.filter_by(email=email).first()

        if user and check_password(password, user.password_hash):
            # Get user permissions
            user_permissions = user.get_permissions()
            
            # Generate Token with role and permissions
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "role": user.role,
                    "permissions": user_permissions,
                    "email": user.email
                }
            )
            return access_token, None
        
        return None, "Invalid email or password"

