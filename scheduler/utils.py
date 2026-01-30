# scheduler/utils.py
import logging
import subprocess
import sys
import os

from config import (
    MAIN_PATH,
    BASE_DIR,
)

def get_logger() -> logging.Logger:
    """Configura y devuelve un logger solo para consola."""
    logger = logging.getLogger("scheduler")

    # Evita añadir handlers duplicados si se llama varias veces
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Solo handler para consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def run_main_script(logger: logging.Logger) -> None:
    """Ejecuta main.py como si hicieras 'python main.py' en la raíz del proyecto."""
    logger.info("Lanzando main.py desde scheduler")
    
    try:
        # Usar Popen para streaming en tiempo real
        process = subprocess.Popen(
            [sys.executable, "-u", str(MAIN_PATH)],  # -u para unbuffered output
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combinar stderr con stdout
            text=True,
            bufsize=1,  # Line buffered
            env={**os.environ, "PYTHONUNBUFFERED": "1"}  # Forzar unbuffered
        )
        
        # Leer y mostrar output en tiempo real línea por línea
        for line in process.stdout:
            line = line.rstrip()
            if line:  # Solo mostrar líneas no vacías
                logger.info(f"[main.py] {line}")
        
        # Esperar a que termine y verificar código de salida
        returncode = process.wait(timeout=3600)
        
        if returncode != 0:
            logger.error(f"main.py terminó con código de error: {returncode}")
            raise subprocess.CalledProcessError(returncode, [sys.executable, str(MAIN_PATH)])
        
        logger.info("main.py terminó correctamente")
        
    except subprocess.TimeoutExpired:
        process.kill()
        logger.error("main.py excedió el tiempo máximo de ejecución (1 hora)")
        raise
    except Exception as e:
        logger.exception(f"Error ejecutando main.py: {e}")
        raise
