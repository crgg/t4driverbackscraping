# app/log_stats.py
import re
from collections import Counter
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Tuple, List

# Mismos nombres que usa writer.save_logs por defecto
LOG_DIR = Path("salida_logs")
NO_CONTROLADOS_PATH = LOG_DIR / "errores_no_controlados.log"
CONTROLADOS_PATH = LOG_DIR / "errores_controlados.log"


def _parse_log_line(line: str):
    """
    Espera líneas tipo:
    ERROR - production - 2025-11-26 14:30:44 - mensaje larguísimo...
    """
    line = line.strip()
    if not line:
        return None

    try:
        level, env, fecha_str, msg = line.split(" - ", 3)
    except ValueError:
        # Formato raro, la saltamos
        return None

    try:
        fecha_dt = datetime.strptime(fecha_str.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    return {
        "level": level.strip(),
        "env": env.strip(),
        "fecha": fecha_dt,
        "mensaje": msg.strip(),
    }

def _firma_mensaje(mensaje: str) -> str:
    """
    Nos quedamos solo con la parte importante del error.
    Cortamos antes de:
      - {"exception":
      - [stacktrace]
      - {"Request : "
    Y, si hay un SQLSTATE=XXXX, nos quedamos hasta ahí.
    """

    # 1) Primero cortamos por exception/stacktrace/Request
    for marker in ('{"exception":', "[stacktrace]", '{"Request : "'):
        pos = mensaje.find(marker)
        if pos != -1:
            mensaje = mensaje[:pos]
            break

    # 2) Si hay un SQLSTATE=XXXX, nos quedamos hasta el final del código
    m = re.search(r"SQLSTATE=\w+", mensaje)
    if m:
        return mensaje[:m.end()].strip()

    # 3) Si no, devolvemos el mensaje tal cual (pero limpiado)
    return mensaje.strip()

def _build_stats(path: Path) -> Dict[str, Dict]:
    """
    Devuelve un dict:
    {
      firma: {
        "total": int,
        "by_date": Counter({date: count}),
        "first": date,
        "last": date,
      },
      ...
    }
    """
    stats: Dict[str, Dict] = {}

    if not path.exists():
        return stats

    with path.open(encoding="utf-8") as f:
        for line in f:
            data = _parse_log_line(line)
            if not data:
                continue

            dt = data["fecha"]
            d_date = dt.date()
            firma = _firma_mensaje(data["mensaje"])

            info = stats.setdefault(
                firma,
                {
                    "total": 0,
                    "by_date": Counter(),
                    "first": dt,
                    "last": dt,
                },
            )

            info["total"] += 1
            info["by_date"][d_date] += 1
            if dt < info["first"]:
                info["first"] = dt
            if dt > info["last"]:
                info["last"] = dt

    return stats


def resumen_por_fecha(
    path: Path,
    dia: date,
    umbral_repetidos: int = 3,
) -> Tuple[int, List[Tuple[str, int]], List[Tuple[str, datetime]]]:
    """
    Devuelve:
      total_hoy, lista_repetidos, lista_nuevos

    - total_hoy: número total de errores ese día
    - repetidos: lista de (firma, count) con count >= umbral_repetidos
    - nuevos: firmas cuya primera aparición en el log es justamente ese día
    
    Args:
        path: ruta del archivo de logs (puede incluir sufijo de app o no)
        dia: fecha
        umbral_repetidos: umbral para considerarse "repetido"
    """
    stats = _build_stats(path)

    total_hoy = 0
    repetidos = []
    nuevos = []

    for firma, info in stats.items():
        n_hoy = info["by_date"].get(dia, 0)
        if not n_hoy:
            continue

        total_hoy += n_hoy

        if n_hoy >= umbral_repetidos:
            repetidos.append((firma, n_hoy))

        if info["first"].date() == dia:
            nuevos.append((firma, info["first"]))

    # Ordenar: repetidos por cantidad (desc), nuevos por fecha (desc)
    repetidos.sort(key=lambda x: x[1], reverse=True)
    nuevos.sort(key=lambda x: x[1], reverse=True)

    return total_hoy, repetidos, nuevos


def url_logs_para_dia(dia: date, app_key: str = "driverapp_goto") -> str:
    """
    Construye la URL a /logs para esa fecha de una aplicación específica.
    
    Args:
        dia: fecha del reporte
        app_key: clave de la aplicación (default: driverapp_goto)
    """
    from .config import get_app_urls
    
    _, _, logs_url = get_app_urls(app_key)
    return f"{logs_url}?date={dia.isoformat()}"


def get_daily_errors(
    path: Path,
    dia: date
) -> List[Dict]:
    """
    Parsea los logs y retorna una lista de errores para el día especificado.
    
    Retorna una lista de dicts con:
    [
        {
            "firma": str,
            "first_time": datetime,
            "count": int
        },
        ...
    ]
    
    Args:
        path: ruta del log
        dia: fecha a filtrar
    """
    stats = _build_stats(path)
    
    daily_errors = []
    
    for firma, info in stats.items():
        # Verificamos si hubo errores este día
        count_today = info["by_date"].get(dia, 0)
        
        if count_today > 0:
            # Necesitamos encontrar la primera ocurrencia *de este día*
            # Como _build_stats solo guarda 'first' global, necesitamos re-escanear o 
            # modificar _build_stats. Pero para no romper lo existente,
            # haremos un escaneo ligero aquí o asumiremos que el sorting en el email 
            # se encargará si guardamos info. 
            # 
            # ERROR: _build_stats no guarda el primer error DEL DIA, guarda el primero GLOBAL.
            # Necesitamos parsear el archivo de nuevo o modificar _build_stats.
            # Dado que leer el archivo es "barato" para estos logs, haremos una lectura filtrada directa.
            pass

    # Re-implementación clean para obtener lo exacto que pide el usuario sin depender de la agregación global
    # que podría perder la hora exacta del primer error DEL DÍA.
    
    errors_map = {} # firma -> {first_time: dt, count: int}
    
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                data = _parse_log_line(line)
                if not data:
                    continue
                
                dt = data["fecha"]
                if dt.date() != dia:
                    continue
                
                firma = _firma_mensaje(data["mensaje"])
                
                if firma not in errors_map:
                    errors_map[firma] = {
                        "firma": firma,
                        "first_time": dt,
                        "count": 0
                    }
                
                errors_map[firma]["count"] += 1
                
                # Actualizar first_time si encontramos uno anterior (aunque log suele ser cronológico)
                if dt < errors_map[firma]["first_time"]:
                    errors_map[firma]["first_time"] = dt

    results = list(errors_map.values())
    
    # Ordenar por fecha de aparición
    results.sort(key=lambda x: x["first_time"])
    
    return results
