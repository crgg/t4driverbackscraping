"""
Helper script to create a regular user account
Usage:
    python create_user.py <email> <password>
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from t4alerts_backend.app import create_app
from t4alerts_backend.common.models import User
from t4alerts_backend.common.database import db
from t4alerts_backend.common.utils import hash_password


def create_user(email, password):
    """Create a new regular user with 'user' role"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            print(f"❌ User with email {email} already exists")
            return False
        
        try:
            # Create new user with 'user' role
            password_hash = hash_password(password)
            new_user = User(
                email=email,
                password_hash=password_hash,
                role='user'
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ User created successfully!")
            print(f"   Email: {email}")
            print(f"   Role: user")
            print(f"\nYou can now login with these credentials.")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating user: {e}")
            return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python create_user.py <email> <password>")
        print("Example: python create_user.py user@example.com password123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    if len(password) < 4:
        print("❌ Password must be at least 4 characters long")
        sys.exit(1)
    
    create_user(email, password)


if __name__ == '__main__':
    main()
