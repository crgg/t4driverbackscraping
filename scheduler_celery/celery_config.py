# scheduler_celery/celery_config.py
"""
Configuración central de Celery: broker, backend, timeouts y beat schedule.
Lee SCHED_ENV del entorno para decidir el intervalo:
  - prod  → cada 7 horas
  - test  → cada 1 minuto
"""
import os
from celery.schedules import crontab

# ──────────────────────────────────────────────
# Broker y backend (Redis)
# ──────────────────────────────────────────────
# Dentro del stack Docker el broker es el servicio "redis".
# Fuera de Docker (ejecución local de prueba) apunta a localhost.
_default_broker = "redis://redis:6379/0"
broker_url        = os.getenv("CELERY_BROKER_URL", _default_broker)
result_backend    = os.getenv("CELERY_RESULT_BACKEND", broker_url)

# ──────────────────────────────────────────────
# Serialización y zona horaria
# ──────────────────────────────────────────────
task_serializer   = "json"
result_serializer = "json"
accept_content    = ["json"]
timezone          = "America/Chicago"   # CST/CDT — zona del proyecto
enable_utc        = True

# ──────────────────────────────────────────────
# Timeouts (evita procesos zombie)
# ──────────────────────────────────────────────
# Hard kill: el worker mata la tarea si supera 1 hora.
task_time_limit      = 3_600   # segundos
# Soft kill: lanza SoftTimeLimitExceeded para un cierre elegante a 55 min.
task_soft_time_limit = 3_300   # segundos

# La tarea no se considera entregada hasta que termine (o muera).
# Evita que una tarea "robada" quede sin ejecutarse si el worker cae.
task_acks_late = True

# ──────────────────────────────────────────────
# Beat schedule — intervalo según entorno
# ──────────────────────────────────────────────
_env = os.getenv("SCHED_ENV", "test").lower()

if _env == "prod":
    # Producción: cada 7 horas a partir del arranque.
    # timedelta es mejor que crontab aquí: si el contenedor se reinicia a las 18:47,
    # ejecuta en ~1 min y luego cada 7 h — no espera la próxima hora fija del reloj.
    from datetime import timedelta
    _schedule = timedelta(hours=7)
    _schedule_str = "cada 7 horas (prod)"
else:
    # Test: cada 1 minuto para validar rápidamente el flujo
    _schedule = crontab(minute="*")
    _schedule_str = "cada 1 minuto (test)"

beat_schedule = {
    "run-scraper-periodic": {
        "task": "scheduler_celery.tasks.run_scraper",
        "schedule": _schedule,
        # Descripción legible en logs
        "options": {"expires": 3_599},   # si nadie consume la tarea en ~1 h, expira
    },
}

# Persistir el estado del beat entre reinicios (evita ejecuciones dobles al reiniciar)
beat_scheduler = "celery.beat.PersistentScheduler"
beat_schedule_filename = "/tmp/celerybeat-schedule"

print(f"[celery_config] SCHED_ENV={_env!r} → schedule: {_schedule_str}")
