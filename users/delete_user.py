"""
Helper script to delete a specific user from the database
Usage:
    python delete_user.py <email>
    python delete_user.py <email> --force  # Skip confirmation
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from t4alerts_backend.app import create_app
from t4alerts_backend.common.models import User
from t4alerts_backend.common.database import db


def delete_user(email, force=False):
    """Delete a user by email"""
    app = create_app()
    
    with app.app_context():
        # Find the user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            print("\n💡 Tip: Run 'python list_users.py' to see all users")
            return False
        
        # Display user information
        role_icon = "👑" if user.role == "admin" else "👤"
        print("\n" + "="*60)
        print(f"🔍 User Found:")
        print("="*60)
        print(f"  {role_icon} Email: {user.email}")
        print(f"  ID: {user.id}")
        print(f"  Role: {user.role}")
        if hasattr(user, 'created_at'):
            print(f"  Created: {user.created_at}")
        print("="*60)
        
        # Confirmation prompt (unless --force flag is used)
        if not force:
            print("\n⚠️  WARNING: This action cannot be undone!")
            confirm = input(f"\nAre you sure you want to delete '{email}'? (yes/no): ").strip().lower()
            
            if confirm not in ['yes', 'y']:
                print("❌ Operation cancelled")
                return False
        
        try:
            # Delete the user
            db.session.delete(user)
            db.session.commit()
            
            print(f"\n✅ User '{email}' has been successfully deleted!")
            print(f"   Role: {user.role}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error deleting user: {e}")
            return False


def main():
    force = False
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python delete_user.py <email>")
        print("  python delete_user.py <email> --force  # Skip confirmation")
        print("\nExample:")
        print("  python delete_user.py user@example.com")
        print("\n💡 Tip: Run 'python list_users.py' to see all users")
        sys.exit(1)
    
    if sys.argv[1] in ['-h', '--help']:
        print("Delete User Script")
        print("\nUsage:")
        print("  python delete_user.py <email>         # Delete with confirmation")
        print("  python delete_user.py <email> --force # Delete without confirmation")
        print("\nExamples:")
        print("  python delete_user.py user@example.com")
        print("  python delete_user.py admin@example.com --force")
        sys.exit(0)
    
    email = sys.argv[1]
    
    # Check for --force flag
    if len(sys.argv) > 2 and sys.argv[2] == '--force':
        force = True
    
    delete_user(email, force)


if __name__ == '__main__':
    main()
