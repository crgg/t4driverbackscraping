# Scheduler de scrapping_project

Este scheduler se encarga de **ejecutar automáticamente `main.py`** (en la carpeta raíz del proyecto) cada cierto tiempo, para que el scrapping de logs y el envío de correos se hagan solos sin intervención manual.

## ¿Qué hace exactamente?

- Usa **APScheduler** dentro de `scheduler/scheduler_main.py`.
- Cada cierto intervalo, el scheduler:
  1. Llama a `python main.py` usando el mismo intérprete que tú estás usando.
  2. `main.py` hace todo el flujo:
     - scrapear logs de las aplicaciones,
     - clasificar errores,
     - guardar en la base de datos / archivos,
     - enviar los correos de resumen.

Mientras el proceso del scheduler esté corriendo, `main.py` se va a ejecutar una y otra vez según el intervalo configurado.

## Estructura relevante

scrapping_project/
  main.py                # punto de entrada de la app (scraping + correos)
  app/                   # lógica de scraping, notificación, etc.
  db/                    # acceso a la base de datos
  scheduler/
    scheduler_main.py    # aquí vive APScheduler (punto de entrada del scheduler)
    config.py            # configuración de intervalos, rutas, entorno (test/prod)
    utils.py             # helpers para ejecutar main.py y manejar logs
    logs/
      scheduler.log      # logs del scheduler
      last_success.txt   # última ejecución correcta de main.py
