"""
SQLAlchemy model for monitored applications.
Handles CRUD operations and credential encryption/decryption.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from t4alerts_backend.common.database import db
from .crypto import get_crypto_service

logger = logging.getLogger(__name__)


class MonitoredApp(db.Model):
    """
    Model representing a dynamically configured application to monitor.
    Credentials are stored encrypted.
    """
    
    __tablename__ = 'monitored_apps'
    
    id = Column(Integer, primary_key=True)
    app_key = Column(String(50), unique=True, nullable=False)
    app_name = Column(String(255), nullable=False)
    base_url = Column(String(500), nullable=False)
    login_path = Column(String(200), default='/login', nullable=False)
    logs_path = Column(String(200), default='/logs', nullable=False)
    username = Column(String(255), nullable=False)  # Encrypted
    password = Column(Text, nullable=False)  # Encrypted
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_credentials: bool = False) -> Dict:
        """
        Convert model to dictionary.
        
        Args:
            include_credentials: If True, includes decrypted credentials (use with caution)
        
        Returns:
            Dictionary representation of the app
        """
        data = {
            'id': self.id,
            'app_key': self.app_key,
            'app_name': self.app_name,
            'base_url': self.base_url,
            'login_path': self.login_path,
            'logs_path': self.logs_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_credentials:
            try:
                username, password = self.get_decrypted_credentials()
                data['username'] = username
                data['password'] = password
            except Exception as e:
                logger.error(f"Failed to decrypt credentials for app {self.app_key}: {e}")
                data['username'] = None
                data['password'] = None
        
        return data
    
    def get_decrypted_credentials(self) -> Tuple[str, str]:
        """
        Decrypt and return the stored credentials.
        
        Returns:
            Tuple of (username, password)
        
        Raises:
            RuntimeError: If decryption fails
        """
        crypto = get_crypto_service()
        return crypto.decrypt_credentials(self.username, self.password)
    
    @classmethod
    def get_all_active(cls) -> List['MonitoredApp']:
        """
        Get all active monitored applications.
        
        Returns:
            List of active MonitoredApp instances
        """
        try:
            apps = cls.query.filter_by(is_active=True).all()
            logger.debug(f"Retrieved {len(apps)} active apps")
            return apps
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving active apps: {e}")
            raise RuntimeError(f"Failed to retrieve active apps: {e}")
    
    @classmethod
    def get_by_key(cls, app_key: str) -> Optional['MonitoredApp']:
        """
        Find an app by its key.
        
        Args:
            app_key: Unique application identifier
        
        Returns:
            MonitoredApp instance or None if not found
        """
        try:
            app = cls.query.filter_by(app_key=app_key).first()
            if app:
                logger.debug(f"Found app with key: {app_key}")
            else:
                logger.debug(f"App not found with key: {app_key}")
            return app
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving app by key {app_key}: {e}")
            raise RuntimeError(f"Failed to retrieve app: {e}")
    
    @classmethod
    def get_by_id(cls, app_id: int) -> Optional['MonitoredApp']:
        """
        Find an app by its ID.
        
        Args:
            app_id: Application ID
        
        Returns:
            MonitoredApp instance or None if not found
        """
        try:
            return cls.query.get(app_id)
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving app by ID {app_id}: {e}")
            raise RuntimeError(f"Failed to retrieve app: {e}")
    
    @classmethod
    def create(cls, data: Dict) -> 'MonitoredApp':
        """
        Create a new monitored app with encrypted credentials.
        
        Args:
            data: Dictionary with app_key, app_name, base_url, username, password, etc.
        
        Returns:
            Newly created MonitoredApp instance
        
        Raises:
            ValueError: If required fields are missing or validation fails
            RuntimeError: If database operation fails
        """
        # Validate required fields
        required_fields = ['app_key', 'app_name', 'base_url', 'username', 'password']
        missing_fields = [f for f in required_fields if not data.get(f)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate app_key doesn't already exist
        if cls.get_by_key(data['app_key']):
            raise ValueError(f"App with key '{data['app_key']}' already exists")
        
        try:
            # Encrypt credentials
            crypto = get_crypto_service()
            encrypted_username, encrypted_password = crypto.encrypt_credentials(
                data['username'],
                data['password']
            )
            
            # Create instance
            app = cls(
                app_key=data['app_key'],
                app_name=data['app_name'],
                base_url=data['base_url'],
                login_path=data.get('login_path', '/login'),
                logs_path=data.get('logs_path', '/logs'),
                username=encrypted_username,
                password=encrypted_password,
                is_active=data.get('is_active', True)
            )
            
            db.session.add(app)
            db.session.commit()
            
            logger.info(f"Created new app: {app.app_key} ({app.app_name})")
            return app
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error creating app: {e}")
            raise ValueError(f"Database constraint violation: {e}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating app: {e}")
            raise RuntimeError(f"Failed to create app: {e}")
    
    @classmethod
    def update(cls, app_id: int, data: Dict) -> 'MonitoredApp':
        """
        Update an existing app.
        
        Args:
            app_id: ID of the app to update
            data: Dictionary with fields to update
        
        Returns:
            Updated MonitoredApp instance
        
        Raises:
            ValueError: If app not found or validation fails
            RuntimeError: If database operation fails
        """
        app = cls.get_by_id(app_id)
        if not app:
            raise ValueError(f"App with ID {app_id} not found")
        
        try:
            # Update basic fields
            if 'app_name' in data:
                app.app_name = data['app_name']
            if 'base_url' in data:
                app.base_url = data['base_url']
            if 'login_path' in data:
                app.login_path = data['login_path']
            if 'logs_path' in data:
                app.logs_path = data['logs_path']
            if 'is_active' in data:
                app.is_active = data['is_active']
            
            # Update credentials if provided
            if 'username' in data or 'password' in data:
                # Get current credentials for defaults
                current_username, current_password = app.get_decrypted_credentials()
                
                new_username = data.get('username', current_username)
                new_password = data.get('password', current_password)
                
                crypto = get_crypto_service()
                encrypted_username, encrypted_password = crypto.encrypt_credentials(
                    new_username,
                    new_password
                )
                
                app.username = encrypted_username
                app.password = encrypted_password
            
            db.session.commit()
            
            logger.info(f"Updated app: {app.app_key}")
            return app
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating app {app_id}: {e}")
            raise RuntimeError(f"Failed to update app: {e}")
    
    @classmethod
    def delete(cls, app_id: int) -> bool:
        """
        Delete an app.
        
        Args:
            app_id: ID of the app to delete
        
        Returns:
            True if deleted successfully
        
        Raises:
            ValueError: If app not found
            RuntimeError: If database operation fails
        """
        app = cls.get_by_id(app_id)
        if not app:
            raise ValueError(f"App with ID {app_id} not found")
        
        try:
            app_key = app.app_key
            db.session.delete(app)
            db.session.commit()
            
            logger.info(f"Deleted app: {app_key}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting app {app_id}: {e}")
            raise RuntimeError(f"Failed to delete app: {e}")
    
    @classmethod
    def to_config_format(cls) -> Dict:
        """
        Convert all active apps to APPS_CONFIG format for compatibility with main.py.
        
        Returns:
            Dictionary in APPS_CONFIG format:
            {
                "app_key": {
                    "name": "App Name",
                    "base_url": "https://example.com",
                    ...
                },
                ...
            }
        """
        try:
            active_apps = cls.get_all_active()
            config = {}
            
            for app in active_apps:
                username, password = app.get_decrypted_credentials()
                
                config[app.app_key] = {
                    "name": app.app_name,
                    "base_url": app.base_url,
                    "login_path": app.login_path,
                    "logs_path": app.logs_path,
                    "username": username,
                    "password": password,
                }
            
            logger.debug(f"Generated config format for {len(config)} apps")
            return config
            
        except Exception as e:
            logger.error(f"Error generating config format: {e}")
            raise RuntimeError(f"Failed to generate config format: {e}")
