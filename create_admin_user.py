"""
Helper script to create an admin user or promote existing user to admin
Usage:
    python create_admin_user.py <email> <password>
    python create_admin_user.py --promote <email>
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from t4alerts_backend.app import create_app
from t4alerts_backend.common.models import User
from t4alerts_backend.common.database import db
from t4alerts_backend.common.utils import hash_password


def create_admin(email, password):
    """Create a new admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            print(f"❌ User with email {email} already exists")
            print(f"   Use --promote flag to promote existing user to admin")
            return False
        
        try:
            # Create new admin user
            password_hash = hash_password(password)
            new_user = User(
                email=email,
                password_hash=password_hash,
                role='admin'
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {email}")
            print(f"   Role: admin")
            print(f"\nYou can now login with these credentials.")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {e}")
            return False


def promote_to_admin(email):
    """Promote existing user to admin"""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ User with email {email} not found")
            return False
        
        if user.role == 'admin':
            print(f"⚠️ User {email} is already an admin")
            return True
        
        try:
            user.role = 'admin'
            db.session.commit()
            
            print(f"✅ User promoted to admin successfully!")
            print(f"   Email: {email}")
            print(f"   Previous role: user")
            print(f"   New role: admin")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error promoting user: {e}")
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create new admin: python create_admin_user.py <email> <password>")
        print("  Promote existing: python create_admin_user.py --promote <email>")
        sys.exit(1)
    
    if sys.argv[1] == '--promote':
        if len(sys.argv) < 3:
            print("❌ Email required for --promote")
            sys.exit(1)
        promote_to_admin(sys.argv[2])
    else:
        if len(sys.argv) < 3:
            print("❌ Email and password required")
            sys.exit(1)
        create_admin(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
