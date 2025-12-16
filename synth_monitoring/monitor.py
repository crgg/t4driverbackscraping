import logging
import time
import requests
from typing import Dict, Any, Optional

from app.config import APPS_CONFIG, get_app_credentials, get_app_urls
from app.session_manager import create_logged_session
from slack_comunication import enviar_aviso_slack
from sms import enviar_aviso_sms

logger = logging.getLogger(__name__)

class SyntheticMonitor:
    """
    Realiza monitoreo sintético (health checks, performance, E2E) de las aplicaciones.
    """

    def __init__(self):
        self.results = {}

    def check_app(self, app_key: str) -> Dict[str, Any]:
        """
        Ejecuta un chequeo completo para una app específica.
        
        Mide:
        - Disponibilidad (Login exitoso)
        - Performance (Tiempo de login)
        - E2E (Acceso a página interna)
        """
        start_time = time.time()
        result = {
            "app_key": app_key,
            "success": False,
            "duration_seconds": 0.0,
            "error": None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        app_name = APPS_CONFIG.get(app_key, {}).get("name", app_key)
        
        try:
            logger.info(f"🩺 Iniciando monitoreo sintético para {app_name}...")
            
            # 1. Disponibilidad & Performance (Login)
            # Reusamos create_logged_session que ya hace requests con retry y valida el login
            session = create_logged_session(app_key, max_retries=2)
            
            # 2. E2E (Verificar acceso a una página interna post-login)
            # Usamos la URL de logs que sabemos que debería existir (aunque esté vacía)
            _, _, logs_url = get_app_urls(app_key)
            resp = session.get(logs_url, timeout=10)
            
            if resp.status_code != 200:
                raise ValueError(f"E2E check failed: {logs_url} returned {resp.status_code}")
                
            duration = time.time() - start_time
            result["success"] = True
            result["duration_seconds"] = round(duration, 2)
            
            logger.info(f"✅ {app_name} OK - Tiempo: {result['duration_seconds']}s")
            
            # Alerta de degradación de performance (ej: si tarda más de 10s)
            if duration > 10.0:
                msg = f"⚠️ Performance Warning: {app_name} login took {duration:.2f}s"
                logger.warning(msg)
                # Opcional: enviar aviso slack si es muy lento
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            result["success"] = False
            result["duration_seconds"] = round(duration, 2)
            result["error"] = error_msg
            
            logger.error(f"❌ {app_name} DOWN - Error: {error_msg}")
            
            # Notificar caída inmediatamente
            self._notify_failure(app_name, error_msg, duration)
            
        return result

    def _notify_failure(self, app_name: str, error: str, duration: float):
        """Envía alertas inmediatas por Slack y SMS."""
        msg_text = (
            f"🚨 *CRITICAL: {app_name} IS DOWN*\n"
            f"❌ Error: `{error}`\n"
            f"⏱️ Duration before fail: {duration:.2f}s\n"
            f"⚠️ Check service status immediately."
        )
        
        # Slack
        enviar_aviso_slack(msg_text)
        
        # SMS (Más breve)
        sms_text = f"🚨 ALERT: {app_name} DOWN. Error: {error[:30]}..."
        enviar_aviso_sms(sms_text)

    def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Ejecuta chequeos para todas las apps configuradas."""
        logger.info("🚀 Iniciando ronda de monitoreo sintético...")
        for app_key in APPS_CONFIG.keys():
            self.results[app_key] = self.check_app(app_key)
        
        return self.results
