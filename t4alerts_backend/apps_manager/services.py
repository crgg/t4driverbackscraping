"""
Business logic layer for app management.
Handles validation, orchestration, and integration with scraping system.
"""
import logging
from datetime import date, datetime
from typing import Dict, List, Optional
from .models import MonitoredApp

logger = logging.getLogger(__name__)


class AppManagerService:
    """
    Service class for managing monitored applications.
    """
    
    @staticmethod
    def list_apps() -> List[Dict]:
        """
        Get all monitored apps (without plaintext passwords).
        
        Returns:
            List of app dictionaries
        """
        try:
            apps = MonitoredApp.query.all()
            logger.info(f"Listed {len(apps)} apps")
            return [app.to_dict(include_credentials=False) for app in apps]
        except Exception as e:
            logger.error(f"Error listing apps: {e}")
            raise RuntimeError(f"Failed to list apps: {e}")
    
    @staticmethod
    def get_app(app_id: int, include_credentials: bool = False) -> Optional[Dict]:
        """
        Get a single app by ID.
        
        Args:
            app_id: Application ID
            include_credentials: If True, includes decrypted credentials
        
        Returns:
            App dictionary or None if not found
        """
        try:
            app = MonitoredApp.get_by_id(app_id)
            if not app:
                logger.warning(f"App not found: {app_id}")
                return None
            
            return app.to_dict(include_credentials=include_credentials)
        except Exception as e:
            logger.error(f"Error getting app {app_id}: {e}")
            raise RuntimeError(f"Failed to get app: {e}")
    
    @staticmethod
    def create_app(data: Dict) -> Dict:
        """
        Create a new monitored app with validation.
        
        Args:
            data: App configuration (app_key, app_name, base_url, username, password, etc.)
        
        Returns:
            Created app dictionary
        
        Raises:
            ValueError: If validation fails
            RuntimeError: If creation fails
        """
        try:
            # Additional validation
            AppManagerService._validate_app_data(data, is_create=True)
            
            # Create app
            app = MonitoredApp.create(data)
            
            logger.info(f"App created successfully: {app.app_key}")
            return app.to_dict(include_credentials=False)
            
        except ValueError as e:
            logger.warning(f"Validation error creating app: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating app: {e}")
            raise RuntimeError(f"Failed to create app: {e}")
    
    @staticmethod
    def update_app(app_id: int, data: Dict) -> Dict:
        """
        Update an existing app.
        
        Args:
            app_id: ID of app to update
            data: Fields to update
        
        Returns:
            Updated app dictionary
        
        Raises:
            ValueError: If validation fails or app not found
            RuntimeError: If update fails
        """
        try:
            # Validate update data
            AppManagerService._validate_app_data(data, is_create=False)
            
            # Update app
            app = MonitoredApp.update(app_id, data)
            
            logger.info(f"App updated successfully: {app.app_key}")
            return app.to_dict(include_credentials=False)
            
        except ValueError as e:
            logger.warning(f"Validation error updating app {app_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating app {app_id}: {e}")
            raise RuntimeError(f"Failed to update app: {e}")
    
    @staticmethod
    def delete_app(app_id: int) -> bool:
        """
        Delete an app.
        
        Args:
            app_id: ID of app to delete
        
        Returns:
            True if deleted successfully
        
        Raises:
            ValueError: If app not found
            RuntimeError: If deletion fails
        """
        try:
            MonitoredApp.delete(app_id)
            logger.info(f"App deleted successfully: {app_id}")
            return True
            
        except ValueError as e:
            logger.warning(f"App not found for deletion: {app_id}")
            raise
        except Exception as e:
            logger.error(f"Error deleting app {app_id}: {e}")
            raise RuntimeError(f"Failed to delete app: {e}")
    
    @staticmethod
    def scan_app(app_id: int, date_str: Optional[str] = None) -> Dict:
        """
        Trigger on-demand scraping for a specific app.
        
        Args:
            app_id: ID of app to scan
            date_str: Optional date string (YYYY-MM-DD), defaults to today
        
        Returns:
            Scraping results dictionary
        
        Raises:
            ValueError: If app not found or date invalid
            RuntimeError: If scraping fails
        """
        try:
            # Get app
            app = MonitoredApp.get_by_id(app_id)
            if not app:
                raise ValueError(f"App with ID {app_id} not found")
            
            # Validate and parse date
            if date_str:
                try:
                    dia = date.fromisoformat(date_str)
                except ValueError:
                    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
            else:
                dia = date.today()
                date_str = dia.isoformat()
            
            logger.info(f"Starting on-demand scan for {app.app_key} on {date_str}")
            
            # Import here to avoid circular dependencies
            from app.scrapper import procesar_aplicacion
            from app.config import APPS_CONFIG
            
            # Get decrypted credentials
            username, password = app.get_decrypted_credentials()
            
            # Build temporary config entry
            temp_config = {
                app.app_key: {
                    "name": app.app_name,
                    "base_url": app.base_url,
                    "login_path": app.login_path,
                    "logs_path": app.logs_path,
                    "username": username,
                    "password": password,
                }
            }
            
            # Temporarily inject into APPS_CONFIG
            original_config = APPS_CONFIG.get(app.app_key)
            APPS_CONFIG[app.app_key] = temp_config[app.app_key]
            
            try:
                # Execute scraping
                resultado = procesar_aplicacion(app.app_key, date_str, dia)
                
                logger.info(f"Scan completed for {app.app_key} on {date_str}")
                
                return {
                    "app_key": app.app_key,
                    "app_name": app.app_name,
                    "date": date_str,
                    "status": "success",
                    "results": {
                        "controlados_nuevos": len(resultado.get('controlados_nuevos', [])),
                        "controlados_avisados": len(resultado.get('controlados_avisados', [])),
                        "no_controlados_nuevos": len(resultado.get('no_controlados_nuevos', [])),
                        "no_controlados_avisados": len(resultado.get('no_controlados_avisados', [])),
                    }
                }
            finally:
                # Restore original config
                if original_config:
                    APPS_CONFIG[app.app_key] = original_config
                else:
                    APPS_CONFIG.pop(app.app_key, None)
                    
        except ValueError as e:
            logger.warning(f"Validation error scanning app: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scanning app {app_id}: {e}")
            raise RuntimeError(f"Failed to scan app: {e}")
    
    @staticmethod
    def export_to_legacy_format() -> Dict:
        """
        Export all active apps to APPS_CONFIG format.
        Used for compatibility with main.py.
        
        Returns:
            Dictionary in APPS_CONFIG format
        """
        try:
            config = MonitoredApp.to_config_format()
            logger.info(f"Exported {len(config)} apps to legacy format")
            return config
        except Exception as e:
            logger.error(f"Error exporting to legacy format: {e}")
            raise RuntimeError(f"Failed to export apps: {e}")
    
    @staticmethod
    def _validate_app_data(data: Dict, is_create: bool = True) -> None:
        """
        Validate app data before create/update.
        
        Args:
            data: App data to validate
            is_create: Whether this is for creation (stricter validation)
        
        Raises:
            ValueError: If validation fails
        """
        # URL validation
        if 'base_url' in data:
            url = data['base_url']
            if not url.startswith(('http://', 'https://')):
                raise ValueError("base_url must start with http:// or https://")
            if url.endswith('/'):
                data['base_url'] = url.rstrip('/')  # Normalize
        
        # Path validation
        for path_field in ['login_path', 'logs_path']:
            if path_field in data:
                path = data[path_field]
                if not path.startswith('/'):
                    raise ValueError(f"{path_field} must start with /")
        
        # App key validation (only for creation)
        if is_create and 'app_key' in data:
            app_key = data['app_key']
            if not app_key.replace('_', '').isalnum():
                raise ValueError("app_key must contain only letters, numbers, and underscores")
            if len(app_key) < 3 or len(app_key) > 50:
                raise ValueError("app_key must be between 3 and 50 characters")
        
        logger.debug(f"App data validation passed")
