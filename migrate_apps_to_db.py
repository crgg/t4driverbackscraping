#!/usr/bin/env python3
"""
Migration script to transfer existing hardcoded apps to the database.
This is a one-time script to populate the monitored_apps table.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from t4alerts_backend.common.database import db
from t4alerts_backend.apps_manager.models import MonitoredApp
from t4alerts_backend.app import create_app
from app.config import APPS_CONFIG_LEGACY


def migrate_apps_to_db():
    """Migrate hardcoded apps from APPS_CONFIG_LEGACY to database."""
    
    print("=" * 60)
    print("  APP CONFIGURATION MIGRATION")
    print("=" * 60)
    print()
    
    # Validate encryption key
    if not os.getenv("ENCRYPTION_KEY"):
        print("❌ ERROR: ENCRYPTION_KEY not found in environment")
        print("   Generate one with:")
        print('   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"')
        print()
        print("   Then add to .env:")
        print("   ENCRYPTION_KEY=your_generated_key")
        return False
    
    # Create Flask app for database context
    app = create_app()
    
    with app.app_context():
        print(f"📋 Found {len(APPS_CONFIG_LEGACY)} apps in legacy config")
        print()
        
        migrated = 0
        skipped = 0
        failed = 0
        
        for app_key, config in APPS_CONFIG_LEGACY.items():
            try:
                # Check if already exists
                existing = MonitoredApp.get_by_key(app_key)
                if existing:
                    print(f"  ⏭️  Skipping {app_key} - already exists in database")
                    skipped += 1
                    continue
                
                # Get credentials from environment
                username = os.getenv(config.get("username_env", ""))
                password = os.getenv(config.get("password_env", ""))
                
                if not username or not password:
                    print(f"  ⚠️  Skipping {app_key} - credentials not found in .env")
                    print(f"      Missing: {config.get('username_env')} or {config.get('password_env')}")
                    failed += 1
                    continue
                
                # Create app entry
                app_data = {
                    "app_key": app_key,
                    "app_name": config["name"],
                    "base_url": config["base_url"],
                    "login_path": config.get("login_path", "/login"),
                    "logs_path": config.get("logs_path", "/logs"),
                    "username": username,
                    "password": password,
                    "is_active": True
                }
                
                MonitoredApp.create(app_data)
                print(f"  ✅ Migrated {app_key} ({config['name']})")
                migrated += 1
                
            except Exception as e:
                print(f"  ❌ Error migrating {app_key}: {e}")
                failed += 1
        
        print()
        print("-" * 60)
        print(f"  Migration Summary:")
        print(f"  • Migrated: {migrated}")
        print(f"  • Skipped (already exists): {skipped}")
        print(f"  • Failed: {failed}")
        print("-" * 60)
        print()
        
        if migrated > 0:
            print("✅ Migration completed successfully!")
            print()
            print("Next steps:")
            print("1. Verify apps in database:")
            print("   psql -U postgres -d t4alerts -c 'SELECT app_key, app_name, is_active FROM monitored_apps;'")
            print()
            print("2. Restart backend to load from database:")
            print("   docker-compose restart backend")
            print()
            return True
        else:
            print("ℹ️  No new apps were migrated")
            return True


if __name__ == "__main__":
    try:
        success = migrate_apps_to_db()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
