# scheduler_celery/celery_app.py
"""
Punto de entrada de la aplicación Celery.
Uso:
  celery -A scheduler_celery.celery_app worker --loglevel=info --concurrency=1
  celery -A scheduler_celery.celery_app beat   --loglevel=info
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto (un nivel arriba de esta carpeta)
_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")

from celery import Celery
import scheduler_celery.celery_config as _cfg

app = Celery("t4alerts_scraper")

# Cargar toda la config desde el módulo celery_config
app.config_from_object(_cfg)

# Auto-descubrir tareas dentro del paquete scheduler_celery
app.autodiscover_tasks(["scheduler_celery"])
