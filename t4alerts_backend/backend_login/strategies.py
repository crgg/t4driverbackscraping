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
            # Generate Token
            # We can store role in claims
            access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
            return access_token, None
        
        return None, "Invalid email or password"
