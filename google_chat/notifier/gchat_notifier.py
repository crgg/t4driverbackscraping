# google_chat/notifier/gchat_notifier.py
"""Main Google Chat notifier orchestrator."""

import logging
from typing import Dict, Any, Optional

from ..core.config import GChatConfig
from ..core.auth import GChatAuthManager
from ..core.logger import get_logger
from ..client.gchat_client import GChatClient
from ..strategies.dm_strategy import DMStrategy
from ..strategies.space_strategy import SpaceStrategy
from ..strategies.base_strategy import NotificationStrategy
from ..errors.exceptions import GChatConfigError, gchat_error_boundary

logger = get_logger(__name__)

# Singleton instance
_gchat_notifier_singleton: Optional['GoogleChatNotifier'] = None


class GoogleChatNotifier:
    """
    Main orchestrator for Google Chat notifications.
    
    Implements Facade pattern to simplify interaction with Google Chat.
    Uses Factory pattern to create appropriate strategy based on configuration.
    
    Attributes:
        config: Google Chat configuration
        client: Google Chat API client
        strategy: Notification strategy (DM, Group, or Space)
    """
    
    def __init__(self, config: Optional[GChatConfig] = None):
        """
        Initialize Google Chat notifier.
        
        Args:
            config: Configuration object (loads from env if not provided)
        """
        # Load config from environment if not provided
        if config is None:
            try:
                config = GChatConfig.from_env()
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                raise GChatConfigError(f"Configuration error: {e}")
        
        self.config = config
        
        # Validate config
        try:
            config.validate()
        except Exception as e:
            logger.error(f"Invalid configuration: {e}")
            raise GChatConfigError(f"Invalid configuration: {e}")
        
        # Initialize auth and client
        if config.enabled:
            try:
                self.auth_manager = GChatAuthManager(config.credentials_path)
                self.client = GChatClient(self.auth_manager)
                self.strategy = self._create_strategy()
                logger.info(f"✓ Google Chat notifier initialized: {self.strategy.get_target()}")
            except Exception as e:
                logger.error(f"Failed to initialize notifier: {e}")
                raise
        else:
            logger.info("Google Chat notifications disabled (GCHAT_ENABLED=0)")
            self.client = None
            self.strategy = None
    
    def _create_strategy(self) -> NotificationStrategy:
        """
        Factory method to create appropriate notification strategy.
        
        Returns:
            NotificationStrategy instance
            
        Raises:
            GChatConfigError: If mode is invalid
        """
        mode = self.config.notification_mode
        
        if mode == 'dm':
            if not self.config.target_email:
                raise GChatConfigError("target_email required for DM mode")
            return DMStrategy(self.config.target_email)
        
        elif mode == 'space':
            if not self.config.space_name:
                raise GChatConfigError("space_name required for Space mode")
            return SpaceStrategy(
                self.config.space_name,
                thread_key=self.config.thread_key
            )
        
        elif mode == 'group':
            # Future: Implement GroupStrategy
            raise GChatConfigError("Group mode not yet implemented")
        
        else:
            raise GChatConfigError(f"Invalid notification mode: {mode}")
    
    @gchat_error_boundary
    def send_error_notification(self, resultado: Dict[str, Any]) -> bool:
        """
        Send error notification based on resultado from procesar_aplicacion().
        
        Only sends if there are SQL errors detected.
        
        Args:
            resultado: Dict with keys:
                - app_name: Application name
                - app_key: Application key
                - fecha_str: Date string
                - no_controlados_nuevos: List of new uncontrolled errors
                
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.config.enabled:
            logger.debug("Google Chat disabled, skipping notification")
            return False
        
        app_name = resultado.get("app_name", "App")
        no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
        
        # Count SQL errors (reuse strategy's method)
        sql_count = self.strategy._contar_errores_sql(no_controlados_nuevos)
        
        # Only send if there are SQL errors
        if sql_count == 0:
            if len(no_controlados_nuevos) > 0:
                logger.info(
                    f"ℹ️ No Google Chat for {app_name}: "
                    f"No SQL errors among {len(no_controlados_nuevos)} errors"
                )
            return False
        
        # Format message using strategy
        mensaje = self.strategy.format_message(resultado)
        
        # Send using strategy
        success = self.strategy.send(self.client, mensaje)
        
        if success:
            logger.info(
                f"✅ Google Chat sent for {app_name}: "
                f"{sql_count} SQL errors to {self.strategy.get_target()}"
            )
        else:
            logger.warning(f"⚠️ Failed to send Google Chat for {app_name}")
        
        return success
    
    @gchat_error_boundary 
    def send_generic_message(self, mensaje: str) -> bool:
        """
        Send a generic message (not error-specific).
        
        Args:
            mensaje: Message text to send
            
        Returns:
            True if sent successfully
        """
        if not self.config.enabled:
            logger.debug("Google Chat disabled, skipping message")
            return False
        
        success = self.strategy.send(self.client, mensaje)
        
        if success:
            logger.info(f"✅ Generic message sent to {self.strategy.get_target()}")
        else:
            logger.warning("⚠️ Failed to send generic message")
        
        return success


def _get_notifier() -> GoogleChatNotifier:
    """
    Get or create singleton notifier instance.
    
    Returns:
        GoogleChatNotifier singleton
    """
    global _gchat_notifier_singleton
    
    if _gchat_notifier_singleton is None:
        try:
            _gchat_notifier_singleton = GoogleChatNotifier()
            logger.debug("✓ Notifier singleton created")
        except Exception as e:
            logger.error(f"Failed to create notifier: {e}")
            # Create a disabled notifier to prevent repeated errors
            config = GChatConfig(
                enabled=False,
                credentials_path="",
                notification_mode="dm"
            )
            _gchat_notifier_singleton = GoogleChatNotifier(config)
    
    return _gchat_notifier_singleton


def enviar_gchat_errores_no_controlados(resultado: Dict[str, Any]) -> bool:
    """
    Send Google Chat notification for SQL errors.
    
    Mirrors sms.enviar_sms_errores_no_controlados() interface.
    
    Args:
        resultado: Dict from procesar_aplicacion() with keys:
            - app_name: Application name
            - app_key: Application key
            - dia: Date object
            - fecha_str: Date string
            - no_controlados_nuevos: List of new uncontrolled errors
            
    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        notifier = _get_notifier()
        return notifier.send_error_notification(resultado)
    except Exception as e:
        logger.error(f"Error in enviar_gchat_errores_no_controlados: {e}")
        return False


def enviar_aviso_gchat(mensaje: str) -> bool:
    """
    Send a generic Google Chat message.
    
    Mirrors sms.enviar_aviso_sms() interface.
    
    Args:
        mensaje: Message text to send
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        notifier = _get_notifier()
        return notifier.send_generic_message(mensaje)
    except Exception as e:
        logger.error(f"Error in enviar_aviso_gchat: {e}")
        return False
