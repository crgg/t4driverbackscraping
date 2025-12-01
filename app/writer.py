# app/writer.py
from pathlib import Path
from typing import Iterable, Optional


def save_logs(
    controlados: Iterable[str],
    no_controlados: Iterable[str],
    output_dir: str = "salida_logs",
    archivo_controlados: str = "errores_controlados.log",
    archivo_no_controlados: str = "errores_no_controlados.log",
    mode: str = "a",
    app_key: Optional[str] = None,
) -> None:
    """
    Guarda los logs en dos archivos dentro de output_dir.
    
    Args:
        controlados: iterador de líneas de errores controlados
        no_controlados: iterador de líneas de errores no controlados
        output_dir: directorio donde guardar los logs
        archivo_controlados: nombre base del archivo de controlados
        archivo_no_controlados: nombre base del archivo de no controlados
        mode: 'a' para append (default), 'w' para sobrescribir
        app_key: (Opcional) clave de la app. Si se proporciona, agrega sufijo a los archivos
                 Ej: app_key='klc' → 'errores_controlados_klc.log'
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Agregar sufijo de app si se proporciona
    if app_key:
        # "errores_controlados.log" → "errores_controlados_klc.log"
        base_c, ext_c = archivo_controlados.rsplit('.', 1) if '.' in archivo_controlados else (archivo_controlados, '')
        base_nc, ext_nc = archivo_no_controlados.rsplit('.', 1) if '.' in archivo_no_controlados else (archivo_no_controlados, '')
        
        archivo_controlados = f"{base_c}_{app_key}.{ext_c}" if ext_c else f"{base_c}_{app_key}"
        archivo_no_controlados = f"{base_nc}_{app_key}.{ext_nc}" if ext_nc else f"{base_nc}_{app_key}"

    controlados_path = output_path / archivo_controlados
    no_controlados_path = output_path / archivo_no_controlados

    with controlados_path.open(mode, encoding="utf-8") as f:
        for line in controlados:
            f.write(line + "\n")

    with no_controlados_path.open(mode, encoding="utf-8") as f:
        for line in no_controlados:
            f.write(line + "\n")
