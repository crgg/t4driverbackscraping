# Scheduler - Ejecución Automática de main.py

Este módulo ejecuta `main.py` automáticamente en intervalos configurados.

---

## � ¿Qué hace scheduler_main.py?

Cuando se ejecuta `scheduler_main.py`, ocurre lo siguiente:

### 1️⃣ Primera Ejecución Inmediata
- Al iniciar, ejecuta `main.py` **inmediatamente** una vez
- Esto asegura que se envíen correos al momento de arrancar el scheduler

### 2️⃣ Programación de Ejecuciones Recurrentes
- Configura un scheduler (APScheduler) para ejecutar `main.py` en intervalos regulares
- El intervalo se define en `config.py` según el entorno:
  - **Test**: cada 1 minuto (por defecto)
  - **Prod**: cada 4 horas (configurable)

### 3️⃣ Ejecución de main.py
Cada vez que se ejecuta el job:
1. Lanza `main.py` como un subproceso
2. Captura toda la salida (stdout y stderr)
3. Escribe los logs en `scheduler/scheduler.log`
4. Si tiene éxito, actualiza `last_success.txt` con la fecha/hora
5. Si falla, registra el error en el log

---

## � Archivos del Scheduler

- **`scheduler_main.py`**: Script principal que ejecuta el scheduler
- **`config.py`**: Configuración de intervalos y rutas
- **`utils.py`**: Funciones auxiliares (logging, ejecución de main.py)
- **`scheduler.log`**: Log de todas las ejecuciones (rotación automática, máx 1MB)
- **`scheduler.err`**: Errores del scheduler (si los hay)
- **`last_success.txt`**: Timestamp de la última ejecución exitosa

---

## � Configuración de Intervalos

El intervalo de ejecución se configura en `config.py`:

```python
# Para cambiar el entorno, exporta la variable:
# export SCHED_ENV=prod

if ENV == "prod":
    INTERVAL = {"hours": 4}  # Cada 4 horas en producción
else:
    INTERVAL = {"minutes": 1}  # Cada 1 minuto en test
```

Puedes modificar `INTERVAL` según tus necesidades. Formatos aceptados:
- `{"minutes": 30}` - Cada 30 minutos
- `{"hours": 2}` - Cada 2 horas
- `{"days": 1}` - Cada día
- `{"hours": 7, "minutes": 30}` - Cada 7 horas y 30 minutos

---

## 📊 Logs y Monitoreo

### Ver logs en tiempo real
```bash
tail -f scheduler/scheduler.log
```

### Ver última ejecución exitosa
```bash
cat scheduler/last_success.txt
```

### Ver errores
```bash
tail -f scheduler/scheduler.err
```

---

## 🔄 Flujo de Ejecución

```
scheduler_main.py inicia
    │
    ├─→ Ejecuta main.py inmediatamente (primera vez)
    │   └─→ Captura logs → scheduler.log
    │   └─→ Guarda timestamp → last_success.txt
    │
    └─→ Configura scheduler con intervalo
        └─→ Cada X minutos/horas:
            ├─→ Ejecuta main.py
            ├─→ Captura logs → scheduler.log
            └─→ Guarda timestamp → last_success.txt
```

---

## ⚙️ Rotación de Logs

Los logs en `scheduler.log` tienen rotación automática:
- **Tamaño máximo**: 1 MB por archivo
- **Backups**: Mantiene las últimas 5 versiones
- **Archivos**: `scheduler.log`, `scheduler.log.1`, `scheduler.log.2`, etc.

Esto evita que los logs crezcan indefinidamente.

---

## 💡 Notas Importantes

- El scheduler usa **BlockingScheduler**, lo que significa que corre en primer plano
- Si se detiene el proceso, las ejecuciones programadas se detienen
- Cada ejecución de `main.py` tiene un timeout de **1 hora máximo**
- Si `main.py` falla, el error se registra pero el scheduler continúa ejecutándose
- La primera ejecución es **siempre inmediata** al arrancar el scheduler
