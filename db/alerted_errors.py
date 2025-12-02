# db/alerted_errors.py
from datetime import date
from typing import Iterable, Set

from .connection import get_cursor


def init_db() -> None:
    """
    Crea la tabla de errores avisados si no existe.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alerted_errors (
                id SERIAL PRIMARY KEY,
                app_key   TEXT NOT NULL,
                fecha     DATE NOT NULL,
                tipo      TEXT NOT NULL,        -- 'controlado' / 'no_controlado'
                signature TEXT NOT NULL,
                first_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (app_key, fecha, tipo, signature)
            );
            """
        )


def get_alerted_signatures(
    app_key: str,
    fecha: date,
    tipo: str,
) -> Set[str]:
    """
    Devuelve las firmas de errores que ya fueron avisados
    para esa app + fecha + tipo.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT signature
            FROM alerted_errors
            WHERE app_key = %s
              AND fecha   = %s
              AND tipo    = %s
            """,
            (app_key, fecha, tipo),
        )
        rows = cur.fetchall()
    return {r[0] for r in rows}


def add_alerted_signatures(
    app_key: str,
    fecha: date,
    tipo: str,
    signatures: Iterable[str],
) -> None:
    """
    Marca en BD esas firmas como ya avisadas (idempotente).
    """
    signatures = list(signatures)
    if not signatures:
        return

    with get_cursor() as cur:
        for sig in signatures:
            cur.execute(
                """
                INSERT INTO alerted_errors (app_key, fecha, tipo, signature)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (app_key, fecha, tipo, signature) DO NOTHING;
                """,
                (app_key, fecha, tipo, sig),
            )

# 🔴 NUEVO: reset total de la memoria de errores avisados
def reset_all_alerted_errors() -> None:
    """
    Borra TODOS los registros de alerted_errors.
    Útil para forzar que TODO se considere 'nuevo' otra vez.
    """
    with get_cursor() as cur:
        cur.execute("TRUNCATE TABLE alerted_errors;")


# 🔴 OPCIONAL: reset solo para una fecha concreta
def reset_alerted_errors_for_date(fecha: date) -> None:
    """
    Borra todos los registros de alerted_errors para una fecha específica.
    """
    with get_cursor() as cur:
        cur.execute("DELETE FROM alerted_errors WHERE fecha = %s;", (fecha,))
