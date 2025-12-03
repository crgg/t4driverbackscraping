#!/bin/bash

# 1) Ir a la carpeta del proyecto
cd /Users/administrator/Desktop/scrapping_project || exit 1

# 2) Escribir en el log que comenzó una ejecución (para saber si vino de cron)
echo "=== EJECUCIÓN $(date) ===" >> temporizador/cron_run.log

# 3) Levantar Postgres (si ya está arriba, no pasa nada)
/usr/local/bin/docker-compose up -d postgres

# 4) Ejecutar main.py con el Python del entorno backend
/opt/anaconda3/envs/backend/bin/python main.py >> temporizador/cron_run.log 2>&1
