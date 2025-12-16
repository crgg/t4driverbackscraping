
import sys
import logging
import os
from datetime import datetime

# Agregar directorio raíz al path para importar módulos app, etc.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from synth_monitoring.monitor import SyntheticMonitor
from app.config import APPS_CONFIG

# Configuración básica de logging para ver output en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print(f"\n🔭 Iniciando Monitoreo Sintético - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Objetivos: {len(APPS_CONFIG)} aplicaciones\n")
    
    monitor = SyntheticMonitor()
    results = monitor.run_all_checks()
    
    print("\n📊 Resumen de Resultados:")
    print("=" * 70)
    print(f"{'Aplicación':<25} | {'Estado':<10} | {'Tiempo (s)':<10} | {'Error'}")
    print("-" * 70)
    
    any_failure = False
    for app_key, res in results.items():
        app_name = APPS_CONFIG.get(app_key, {}).get("name", app_key)
        # Recortar nombre si es muy largo
        if len(app_name) > 23:
            app_name = app_name[:20] + "..."
            
        status = "✅ ONLINE" if res["success"] else "❌ OFFLINE"
        error = res["error"] if res["error"] else ""
        
        # Colorizar salida si es posible (opcional, aqui simple texto)
        print(f"{app_name:<25} | {status:<10} | {res['duration_seconds']:<10} | {error}")
        
        if not res["success"]:
            any_failure = True
            
    print("=" * 70)
    
    if any_failure:
        print("\n⚠️ Se detectaron problemas en una o más aplicaciones.")
        print("   Las alertas han sido enviadas vía Slack/SMS.")
        sys.exit(1)
    else:
        print("\n✅ Todos los sistemas operativos y respondiendo correctamente.")
        sys.exit(0)

if __name__ == "__main__":
    main()
