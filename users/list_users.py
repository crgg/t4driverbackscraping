"""
Helper script to list all users in the database
Usage:
    python list_users.py
    python list_users.py --admins-only  # Show only admin users
    python list_users.py --users-only   # Show only regular users
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from t4alerts_backend.app import create_app
from t4alerts_backend.common.models import User
from t4alerts_backend.common.database import db


def list_users(filter_role=None):
    """List all users in the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Query users based on filter
            if filter_role:
                users = User.query.filter_by(role=filter_role).all()
            else:
                users = User.query.all()
            
            if not users:
                if filter_role:
                    print(f"📋 No {filter_role} users found in database")
                else:
                    print("📋 No users found in database")
                return
            
            # Display header
            print("\n" + "="*80)
            if filter_role:
                print(f"📋 {filter_role.upper()} USERS IN DATABASE")
            else:
                print("📋 ALL USERS IN DATABASE")
            print("="*80)
            
            # Display users
            for i, user in enumerate(users, 1):
                role_icon = "👑" if user.role == "admin" else "👤"
                print(f"\n{i}. {role_icon} {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Role: {user.role}")
                print(f"   Created: {user.created_at if hasattr(user, 'created_at') else 'N/A'}")
            
            print("\n" + "="*80)
            
            # Display summary
            total = len(users)
            if not filter_role:
                admin_count = sum(1 for u in users if u.role == 'admin')
                user_count = sum(1 for u in users if u.role == 'user')
                print(f"Total users: {total} (👑 {admin_count} admins, 👤 {user_count} regular users)")
            else:
                print(f"Total {filter_role} users: {total}")
            
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
            return


def main():
    filter_role = None
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--admins-only':
            filter_role = 'admin'
        elif sys.argv[1] == '--users-only':
            filter_role = 'user'
        elif sys.argv[1] in ['-h', '--help']:
            print("Usage:")
            print("  python list_users.py              # List all users")
            print("  python list_users.py --admins-only # List only admin users")
            print("  python list_users.py --users-only  # List only regular users")
            sys.exit(0)
        else:
            print(f"❌ Unknown option: {sys.argv[1]}")
            print("Use --help to see available options")
            sys.exit(1)
    
    list_users(filter_role)


if __name__ == '__main__':
    main()
