import sys
from unittest.mock import MagicMock

# Mock dotenv before importing app modules that use it
sys.modules["dotenv"] = MagicMock()

import os
from datetime import datetime, date
from pathlib import Path

# Mock config to avoid RuntimeError on missing env vars
mock_config = MagicMock()
mock_config.get_app_urls.return_value = ("url1", "url2", "http://logs.com")
sys.modules["app.config"] = mock_config

from app.email_notifier import construir_html_resumen

# Setup dummy logs
LOG_DIR = Path("salida_logs")
LOG_DIR.mkdir(exist_ok=True)

NC_LOG = LOG_DIR / "errores_no_controlados_demo.log"
C_LOG = LOG_DIR / "errores_controlados_demo.log"

def create_logs():
    today = date.today().isoformat()
    # No Controlados
    nc_content = f"""
ERROR - production - {today} 09:49:25 - SQLSTATE[40001]: Serialization failure: -911 [IBM][CLI Driver][DB2/NT64] SQL0911N The current transaction has been rolled back because of a deadlock or timeout. Reason code "68". SQLSTATE=40001
    """
    with open(NC_LOG, "w") as f:
        f.write(nc_content.strip())

    # Controlados
    with open(C_LOG, "w") as f:
        f.write("")

def verify():
    create_logs()
    
    nc_target = LOG_DIR / "errores_no_controlados_teststyle.log"
    c_target = LOG_DIR / "errores_controlados_teststyle.log"
    
    if NC_LOG.exists(): os.rename(NC_LOG, nc_target)
    if C_LOG.exists(): os.rename(C_LOG, c_target)
        
    print(f"Testing with logs: {nc_target}, {c_target}")
    
    html, _, _ = construir_html_resumen(date.today(), app_name="GoTo Logistics", app_key="teststyle")
    
    print("-" * 40)
    print(html)
    print("-" * 40)
    
    # Verification assertions for styling
    # 1. Header black (no style="color: blue;")
    assert "<h2>Company: GoTo Logistics" in html, "Header content match"
    assert 'style="color: blue;"' not in html.split('\n')[0], "Header should NOT correspond to blue style"

    # 2. Errores (no controlados) -> Errores (red)
    assert '<span style="color: red;">Errores</span>' in html, "Should have red 'Errores' title"
    
    # 3. Errores (controlados) (blue)
    assert '<span style="color: blue;">Errores (controlados)</span>' in html, "Should have blue 'Errores (controlados)' title"
    
    print("\n✅ Verification Successful!")
    
    if nc_target.exists(): os.remove(nc_target)
    if c_target.exists(): os.remove(c_target)

if __name__ == "__main__":
    verify()
