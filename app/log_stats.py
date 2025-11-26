# app/log_stats.py
from collections import Counter
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Tuple, List

from .config import BASE_URL, LOGS_PATH

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

    Así, por ejemplo:
      - errores de DB se quedan en el SQLSTATE...
      - errores controlados se quedan en 'Error: Parameter Empty - avatars 3'
    """
    for marker in ('{"exception":', "[stacktrace]", '{"Request : "'):
        pos = mensaje.find(marker)
        if pos != -1:
            return mensaje[:pos].strip()

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

            d = data["fecha"].date()
            firma = _firma_mensaje(data["mensaje"])

            info = stats.setdefault(
                firma,
                {
                    "total": 0,
                    "by_date": Counter(),
                    "first": d,
                    "last": d,
                },
            )

            info["total"] += 1
            info["by_date"][d] += 1
            if d < info["first"]:
                info["first"] = d
            if d > info["last"]:
                info["last"] = d

    return stats


def resumen_por_fecha(
    path: Path,
    dia: date,
    umbral_repetidos: int = 3,
) -> Tuple[int, List[Tuple[str, int]], List[Tuple[str, int]]]:
    """
    Devuelve:
      total_hoy, lista_repetidos, lista_nuevos

    - total_hoy: número total de errores ese día
    - repetidos: lista de (firma, count) con count >= umbral_repetidos
    - nuevos: firmas cuya primera aparición en el log es justamente ese día
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

        if info["first"] == dia:
            nuevos.append((firma, n_hoy))

    # Ordenar de más a menos frecuente
    repetidos.sort(key=lambda x: x[1], reverse=True)
    nuevos.sort(key=lambda x: x[1], reverse=True)

    return total_hoy, repetidos, nuevos


def url_logs_para_dia(dia: date) -> str:
    """
    Construye la URL a /logs para esa fecha.
    """
    return f"{BASE_URL}{LOGS_PATH}?date={dia.isoformat()}"
