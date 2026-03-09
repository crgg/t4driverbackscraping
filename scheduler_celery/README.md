# scheduler_celery — Scheduler de T4Alerts con Celery + Redis + Docker

Este directorio reemplaza la carpeta `scheduler/` (APScheduler), que quedó en desuso tras el incidente de ransomware del 7-9 de marzo de 2026.

## Por qué se migró

| Problema anterior | Solución actual |
|---|---|
| `ModuleNotFoundError: No module named 'apscheduler'` | Entorno inmutable en contenedor Docker |
| `max instances reached` (proceso zombie) | `--concurrency=1` + `task_time_limit=3600` |
| Dependencia de `launchd` y Python del host | `restart: always` en Docker Compose |
| Sin visibilidad si el scraper falló | Flower en `:5555` + Redis backend |

---

## Estructura

```
scheduler_celery/
├── __init__.py          # paquete Python
├── celery_app.py        # instancia Celery (punto de entrada)
├── celery_config.py     # configuración: broker, timeouts, beat schedule
├── tasks.py             # tarea run_scraper con retry + exponential backoff
├── Dockerfile           # imagen Python (contexto = raíz del proyecto)
├── docker-compose.yml   # redis + worker + beat + flower
└── README.md            # este archivo
```

---

## Variables de entorno clave

Todas se leen del `.env` raíz del proyecto (no necesita duplicarse).

| Variable | Valores | Efecto |
|---|---|---|
| `SCHED_ENV` | `prod` / `test` | `prod` → cada 7 h · `test` → cada 1 min |
| `CELERY_BROKER_URL` | (auto) | Se sobreescribe en docker-compose |
| `SCRAPER_TIMEOUT` | `3600` (default) | Timeout del subproceso en segundos |
| `RETRY_BASE_MINUTES` | `5` (default) | Minutos base para backoff (5 → 10 → 20) |

---

## Comandos de uso

### Arranque (producción)

```bash
cd /Users/administrator/Desktop/scrapping_project/scheduler_celery

# Asegúrate que SCHED_ENV=prod en .env
docker compose up -d --build
```

### Arranque rápido (test — ejecución cada 1 minuto)

```bash
SCHED_ENV=test docker compose up --build
# o edita .env → SCHED_ENV=test antes de levantar
```

### Ver logs en tiempo real

```bash
docker compose logs -f worker beat
```

### Parada completa

```bash
docker compose down
# Con borrado de volúmenes (reinicia el estado del beat):
docker compose down -v
```

### Reiniciar solo el worker (sin bajar todo el stack)

```bash
docker compose restart worker
```

---

## Monitoreo con Flower

Flower es una UI web para ver el estado de tareas, workers y colas.

- **URL:** [http://localhost:5555](http://localhost:5555)
- **Credenciales:** `admin` / `t4alerts`

Si no necesitas Flower, comenta el servicio `flower` en `docker-compose.yml`.

---

## Lógica de retry y tolerancia a fallos

Si `main.py` falla (cualquier excepción o código de salida ≠ 0), Celery reintenta automáticamente:

```
Intento 1 falla  →  espera  5 min  →  Intento 2
Intento 2 falla  →  espera 10 min  →  Intento 3
Intento 3 falla  →  espera 20 min  →  Intento 4 (último)
Intento 4 falla  →  FAILURE (traceback en Redis/Flower)
```

El worker está configurado con `acks_late=True`: la tarea no se confirma como entregada hasta completarse, así que si el worker muere durante la ejecución, la tarea se re-encola.

---

## launchd (arranque automático del Mac)

El plist `launchd_execution/com.user.logscraper.plist` fue actualizado para ejecutar `docker compose up --build` en lugar de `scheduler_main.py`. **`RunAtLoad` está en `false`** porque Docker Desktop puede no estar listo al boot.

### Para activar el arranque automático:

1. Asegúrate de que Docker Desktop arranque con el sistema (Preferencias → General → "Start Docker Desktop when you log in").
2. Edita el plist y cambia `<false/>` a `<true/>` en `RunAtLoad`.
3. Recarga el agente:

```bash
launchctl unload ~/Library/LaunchAgents/com.user.logscraper.plist
launchctl load  ~/Library/LaunchAgents/com.user.logscraper.plist
```

---

## Carpeta `scheduler/` (legado)

La carpeta `scheduler/` con `scheduler_main.py` + APScheduler se conserva como referencia histórica pero **ya no es invocada por launchd ni por ningún proceso automático**. No la borres si quieres mantener el historial.
