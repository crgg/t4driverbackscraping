# scheduler_celery/tasks.py
"""
Tarea principal de scraping para Celery.

Flujo de resiliencia:
  1. Al arrancar el worker, se dispara run_scraper() INMEDIATAMENTE via worker_ready.
  2. Celery Beat dispara run_scraper() según el intervalo configurado (7 h / 1 min).
  3. El worker ejecuta main.py como subproceso con un timeout estricto de 3600 s.
  4. Si el subproceso falla, la tarea reintenta con exponential backoff:
       - Intento 1: espera 5  minutos  (retry #1)
       - Intento 2: espera 10 minutos  (retry #2)
       - Intento 3: espera 20 minutos  (retry #3)
  5. Tras 3 intentos fallidos, Celery marca la tarea como FAILURE.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from scheduler_celery.celery_app import app

# ──────────────────────────────────────────────
# Logger
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("scheduler_celery.tasks")

# Ruta a main.py (raíz del proyecto, un nivel arriba de esta carpeta)
_BASE_DIR = Path(__file__).resolve().parent.parent
_MAIN_PY  = _BASE_DIR / "main.py"

# Tiempo máximo de ejecución del subproceso (mismo que task_time_limit)
_SUBPROCESS_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "3600"))

# Minutos base para el backoff (se duplica en cada reintento)
_RETRY_BASE_MINUTES = int(os.getenv("RETRY_BASE_MINUTES", "5"))


# ──────────────────────────────────────────────
# Tarea principal
# ──────────────────────────────────────────────
@app.task(
    bind=True,
    name="scheduler_celery.tasks.run_scraper",
    max_retries=3,
    acks_late=True,           # no ACK hasta que la tarea termina (evita pérdida si el worker muere)
    reject_on_worker_lost=True,  # re-encola si el worker muere bruscamente
)
def run_scraper(self: Task) -> dict:
    """
    Ejecuta main.py como subproceso y devuelve un dict con el resultado.
    En caso de fallo reintenta con exponential backoff.
    """
    attempt = self.request.retries + 1
    logger.info(
        "═══════════════════════════════════════════════════════\n"
        f"  Iniciando run_scraper — intento {attempt}/{self.max_retries + 1}\n"
        f"  main.py: {_MAIN_PY}\n"
        "═══════════════════════════════════════════════════════"
    )

    try:
        result = _run_subprocess()
        logger.info(
            f"✅ run_scraper completado exitosamente en intento {attempt}.\n"
            f"   Salida (últimas 10 líneas):\n{result['tail']}"
        )
        return result

    except SoftTimeLimitExceeded:
        # El worker recibió una señal de soft-kill antes del hard-kill
        msg = "⏰ SoftTimeLimitExceeded: main.py superó el límite de tiempo suave."
        logger.error(msg)
        # No reintentamos en timeouts — el estado de la aplicación es desconocido
        raise

    except Exception as exc:
        # Calcular tiempo de espera con exponential backoff
        wait_seconds = _RETRY_BASE_MINUTES * 60 * (2 ** self.request.retries)
        wait_min = wait_seconds // 60

        if self.request.retries < self.max_retries:
            logger.warning(
                f"⚠️  run_scraper falló en intento {attempt}.\n"
                f"   Error: {type(exc).__name__}: {exc}\n"
                f"   Reintentando en {wait_min} minutos (retry #{self.request.retries + 1}/{self.max_retries})…"
            )
            raise self.retry(exc=exc, countdown=wait_seconds)
        else:
            # Último intento agotado
            logger.error(
                f"🚨 run_scraper AGOTÓ LOS {self.max_retries} REINTENTOS.\n"
                f"   Último error: {type(exc).__name__}: {exc}\n"
                "   La tarea queda marcada como FAILURE en Redis. Revisar Celery logs / Flower."
            )
            raise  # Propaga la excepción → tarea queda en estado FAILURE


# ──────────────────────────────────────────────
# Helper interno
# ──────────────────────────────────────────────
def _run_subprocess() -> dict:
    """
    Lanza main.py como subproceso capturando stdout/stderr combinados.
    Lanza excepción si el proceso termina con código ≠ 0 o excede el timeout.
    """
    logger.info(f"Lanzando: {sys.executable} -u {_MAIN_PY}")

    process = subprocess.Popen(
        [sys.executable, "-u", str(_MAIN_PY)],
        cwd=str(_BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # unifica stderr con stdout
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )

    lines = []
    try:
        for raw_line in process.stdout:
            line = raw_line.rstrip()
            if line:
                logger.info(f"[main.py] {line}")
                lines.append(line)
    finally:
        try:
            returncode = process.wait(timeout=_SUBPROCESS_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError(
                f"main.py excedió el timeout de {_SUBPROCESS_TIMEOUT} s y fue terminado forzosamente."
            )

    if returncode != 0:
        tail = "\n".join(lines[-20:]) if lines else "(sin salida)"
        raise subprocess.CalledProcessError(
            returncode,
            [sys.executable, str(_MAIN_PY)],
            output=tail,
        )

    tail = "\n".join(lines[-10:]) if lines else "(sin salida)"
    return {
        "returncode": returncode,
        "lines_captured": len(lines),
        "tail": tail,
    }


# ──────────────────────────────────────────────
# Ejecución inmediata al arrancar el worker
# ──────────────────────────────────────────────
from celery.signals import worker_ready

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Se dispara UNA SOLA VEZ cuando el worker termina de inicializarse.
    Envía run_scraper a la cola con un pequeño delay (10 s) para que
    el worker esté 100% listo antes de aceptar la tarea.

    Esto garantiza: al hacer 'docker compose up', los avisos se envían
    de inmediato sin esperar el intervalo completo (7 h en prod).
    Beat sigue encargándose de las ejecuciones periódicas posteriores.
    """
    logger.info(
        "🚀 Worker listo — enviando run_scraper inmediatamente (countdown=10s) …"
    )
    run_scraper.apply_async(countdown=10)
