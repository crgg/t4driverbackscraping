#!/usr/bin/env python3
"""
Test para comparar contenido de Email vs Google Chat
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from app.email_notifier import construir_html_resumen
from google_chat.notifier import _format_error_message_email_style, _get_log_paths
from app.log_stats import get_daily_errors

# Test con una app - usemos T4TRANS para ver la diferencia
app_key = "t4trans"
app_name = "T4NOTIFICATIONS"
dia_feb_11 = date(2026, 2, 11)
dia_feb_12 = date(2026, 2, 12)

print("="*70)
print("COMPARACIÓN: Email vs Google Chat")
print("="*70)

for test_date in [dia_feb_11, dia_feb_12]:
    print(f"\n{'='*70}")
    print(f"FECHA: {test_date}")
    print(f"{'='*70}")
    
    # EMAIL
    print("\n📧 EMAIL:")
    html, total_nc, total_c = construir_html_resumen(test_date, app_name, app_key)
    
    # La condición de envío de email
    enviar_email = not (total_nc == 0 and total_c == 0)
    
    print(f"   Errores NO controlados: {total_nc}")
    print(f"   Errores controlados: {total_c}")
    print(f"   ✅ Se envía: {'SÍ' if enviar_email else 'NO'}")
    
    # GOOGLE CHAT
    print("\n💬 GOOGLE CHAT:")
    no_controlados_path, controlados_path = _get_log_paths(app_key)
    nc_errors = get_daily_errors(no_controlados_path, test_date)
    c_errors = get_daily_errors(controlados_path, test_date)
    
    message = _format_error_message_email_style(app_name, app_key, test_date, nc_errors, c_errors)
    
    # La condición de envío de Google Chat
    enviar_gchat = message is not None
    
    print(f"   Errores NO controlados: {len(nc_errors)}")
    print(f"   Errores controlados: {len(c_errors)}")
    print(f"   ✅ Se envía: {'SÍ' if enviar_gchat else 'NO'}")
    
    # COMPARACIÓN
    if enviar_email != enviar_gchat:
        print(f"\n   ⚠️ DISCREPANCIA DETECTADA!")
        print(f"      Email se envía: {enviar_email}")
        print(f"      Google Chat se envía: {enviar_gchat}")

print(f"\n{'='*70}")
print("CONCLUSIÓN:")
print("="*70)
print("Email: Se envía si hay CUALQUIER error (controlado o no controlado)")
print("Google Chat: Se envía SOLO si hay errores NO controlados")
print("\nEsto causa que Google Chat no envíe mensajes para apps con")
print("solo errores controlados (como T4TRANS con Firebase errors)")
