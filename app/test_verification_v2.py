from datetime import date, datetime
from pathlib import Path
from app.log_stats import resumen_por_fecha

# Create dummy log file
dummy_log_content = """
ERROR - production - 2025-12-08 08:00:00 - Error type A
ERROR - production - 2025-12-08 08:30:00 - Error type A
ERROR - production - 2025-12-08 09:00:00 - Error type A
ERROR - production - 2025-12-08 10:00:00 - Error type B
"""
test_log_path = Path("test_errores_v2.log")
test_log_path.write_text(dummy_log_content.strip())

# Run stats
today = date(2025, 12, 8)
total, repetidos, nuevos = resumen_por_fecha(test_log_path, today, umbral_repetidos=3)

print(f"Total: {total}")
print("Repetidos:")
for firma, count in repetidos:
    print(f"  {firma}: {count} (Type: {type(count)})")

print("Nuevos:")
for firma, dt in nuevos:
    print(f"  {firma}: {dt} (Type: {type(dt)})")

# Simulate email_notifier logic (same code as in file)
def _html_lista_repetidos(titulo, items):
    if not items:
        return f"<h3>{titulo}</h3><p>Sin elementos.</p>"
    lineas = [f"<h3>{titulo}</h3>", "<ul>"]
    for firma, count in items:
        firma_corta = firma
        lineas.append(f"<li>{firma_corta} <strong>({count} veces)</strong></li>")
    lineas.append("</ul>")
    return "\n".join(lineas)

def _html_lista_nuevos(titulo, items):
    if not items:
        return f"<h3>{titulo}</h3><p>Sin elementos.</p>"
    lineas = [f"<h3>{titulo}</h3>", "<ul>"]
    for firma, first_dt in items:
        fecha_str = first_dt.strftime("%Y-%m-%d %H:%M:%S")
        firma_corta = firma
        lineas.append(f"<li><strong>{fecha_str}</strong> — {firma_corta}</li>")
    lineas.append("</ul>")
    return "\n".join(lineas)

# Test HTML generation
print("\nGenerated HTML (Repetidos):")
print(_html_lista_repetidos("Test Repetidos", repetidos))

print("\nGenerated HTML (Nuevos):")
print(_html_lista_nuevos("Test Nuevos", nuevos))

# Cleanup
test_log_path.unlink()
