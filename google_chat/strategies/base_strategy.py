# google_chat/strategies/base_strategy.py
"""Base notification strategy using Template Method pattern."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..client.gchat_client import GChatClient
from ..core.logger import get_logger

logger = get_logger(__name__)


class NotificationStrategy(ABC):
    """
    Abstract base class for notification strategies.
    
    Implements Template Method pattern for common notification flow.
    Subclasses must implement send() and get_target().
    """
    
    @abstractmethod
    def send(self, client: GChatClient, mensaje: str) -> bool:
        """
        Send notification using specific strategy.
        
        Args:
            client: Google Chat client instance
            mensaje: Message text to send
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_target(self) -> str:
        """
        Return target identifier for logging.
        
        Returns:
            Human-readable target description
        """
        pass
    
    def format_message(self, resultado: Dict[str, Any]) -> str:
        """
        Format error notification message.
        
        Template method that can be overridden by subclasses.
        
        Args:
            resultado: Dict from procesar_aplicacion() with keys:
                - app_name: Application name
                - app_key: Application key
                - fecha_str: Date string
                - no_controlados_nuevos: List of new uncontrolled errors
                
        Returns:
            Formatted message text
        """
        from app.config import get_sms_app_name
        
        app_key = resultado.get("app_key", "unknown")
        app_name = get_sms_app_name(app_key)
        fecha_str = resultado.get("fecha_str", "N/A")
        no_controlados_nuevos = resultado.get("no_controlados_nuevos", [])
        
        # Count SQL errors
        sql_count = self._contar_errores_sql(no_controlados_nuevos)
        
        # Build rich message (Google Chat supports markdown)
        plural = 's' if sql_count != 1 else ''
        mensaje = (
            f"🚨 **{app_name}**: {sql_count} SQL error{plural}\n\n"
            f"⚠️ Check logs immediately\n"
            f"📅 Fecha: {fecha_str}\n"
            f"📊 Errores totales: {len(no_controlados_nuevos)}"
        )
        
        return mensaje
    
    def _contar_errores_sql(self, errores: list) -> int:
        """
        Count SQL errors in error list.
        
        Args:
            errores: List of error messages
            
        Returns:
            Count of SQL-related errors
        """
        count = 0
        for error in errores:
            error_lower = error.lower()
            if any(keyword in error_lower for keyword in ['sql', 'sqlstate', 'database', 'pdo']):
                count += 1
        return count
