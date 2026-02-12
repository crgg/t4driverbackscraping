#!/usr/bin/env python3
"""
Script para verificar si T4TRANS está truncando los archivos de log
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logs_scraper import fetch_logs_html
from app.session_manager import create_logged_session
from datetime import date

# Autenticar
session = create_logged_session("t4trans")
print("✅ Autenticación exitosa")

# Fetch logs
fecha_str = "2026-02-11"
logs_html = fetch_logs_html(session, fecha_str, "t4trans")

print(f"\n📊 Análisis del contenido descargado:")
print(f"Tamaño total: {len(logs_html):,} bytes ({len(logs_html)/1024:.2f} KB)")

# Verificar si está truncado
if "Showing last" in logs_html:
    import re
    match = re.search(r'Showing last.*?(\d+)', logs_html)
    if match:
        print(f"\n⚠️ ARCHIVO TRUNCADO!")
        print(f"   Mensaje del servidor: 'Showing last {int(match.group(1)):,} bytes'")
        print(f"   Esto significa que NO estamos viendo todo el archivo.")
else:
    print("\n✅ No se detectó mensaje de truncamiento")

# Analizar timestamps
import re
timestamps = re.findall(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', logs_html)
print(f"\n📝 Entradas de log encontradas: {len(timestamps)}")

if timestamps:
    print(f"Primera entrada: {timestamps[0]}")
    print(f"Última entrada: {timestamps[-1]}")
    
    from datetime import datetime
    first_dt = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
    last_dt = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
    
    print(f"\n⏱️ Cobertura temporal:")
    print(f"   Desde: {first_dt.strftime('%H:%M:%S')}")
    print(f"   Hasta: {last_dt.strftime('%H:%M:%S')}")
    print(f"   Duración: {(last_dt - first_dt).total_seconds() / 3600:.1f} horas")
    
    if first_dt.hour > 6:
        print(f"\n⚠️ PROBLEMA DETECTADO:")
        print(f"   Los logs empiezan a las {first_dt.strftime('%H:%M')}, NO desde 00:00")
        print(f"   Esto confirma que el archivo está truncado y faltan logs del inicio del día")
