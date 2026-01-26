"""
Helper script to delete all users from the database
⚠️  DANGER: This will delete ALL users, including admins!
Usage:
    python delete_all_users.py
    python delete_all_users.py --exclude-admins  # Keep admin users
    python delete_all_users.py --force           # Skip confirmation
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from t4alerts_backend.app import create_app
from t4alerts_backend.common.models import User
from t4alerts_backend.common.database import db


def delete_all_users(exclude_admins=False, force=False):
    """Delete all users from the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Query users to delete
            if exclude_admins:
                users = User.query.filter_by(role='user').all()
            else:
                users = User.query.all()
            
            if not users:
                if exclude_admins:
                    print("📋 No regular users found in database")
                else:
                    print("📋 No users found in database")
                return
            
            # Display users that will be deleted
            print("\n" + "="*70)
            if exclude_admins:
                print("⚠️  THE FOLLOWING REGULAR USERS WILL BE DELETED:")
            else:
                print("⚠️  THE FOLLOWING USERS WILL BE DELETED:")
            print("="*70)
            
            admin_count = 0
            user_count = 0
            
            for i, user in enumerate(users, 1):
                role_icon = "👑" if user.role == "admin" else "👤"
                print(f"{i}. {role_icon} {user.email} (Role: {user.role})")
                
                if user.role == 'admin':
                    admin_count += 1
                else:
                    user_count += 1
            
            print("="*70)
            print(f"Total to delete: {len(users)}", end="")
            if not exclude_admins and admin_count > 0:
                print(f" (👑 {admin_count} admins, 👤 {user_count} regular users)")
            else:
                print()
            print("="*70)
            
            # Confirmation prompt (unless --force flag is used)
            if not force:
                print("\n🚨 DANGER: This action cannot be undone!")
                
                if not exclude_admins and admin_count > 0:
                    print("⚠️  You are about to delete ADMIN users as well!")
                
                confirm = input("\nType 'DELETE ALL' to confirm: ").strip()
                
                if confirm != 'DELETE ALL':
                    print("❌ Operation cancelled")
                    return False
            
            # Delete all users
            deleted_count = 0
            for user in users:
                db.session.delete(user)
                deleted_count += 1
            
            db.session.commit()
            
            print(f"\n✅ Successfully deleted {deleted_count} user(s)!")
            
            if exclude_admins:
                remaining = User.query.filter_by(role='admin').count()
                print(f"   {remaining} admin user(s) remain in the database")
            else:
                print("   The users table is now empty")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error deleting users: {e}")
            return False


def main():
    exclude_admins = False
    force = False
    
    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == '--exclude-admins':
            exclude_admins = True
        elif arg == '--force':
            force = True
        elif arg in ['-h', '--help']:
            print("Delete All Users Script")
            print("\n⚠️  DANGER: This script deletes users from the database!")
            print("\nUsage:")
            print("  python delete_all_users.py                 # Delete ALL users (with confirmation)")
            print("  python delete_all_users.py --exclude-admins # Delete only regular users")
            print("  python delete_all_users.py --force         # Skip confirmation (dangerous!)")
            print("\nExamples:")
            print("  python delete_all_users.py")
            print("  python delete_all_users.py --exclude-admins")
            print("  python delete_all_users.py --exclude-admins --force")
            print("\n💡 Tip: Run 'python list_users.py' first to see what will be deleted")
            sys.exit(0)
        else:
            print(f"❌ Unknown option: {arg}")
            print("Use --help to see available options")
            sys.exit(1)
    
    delete_all_users(exclude_admins, force)


if __name__ == '__main__':
    main()
