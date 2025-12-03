# db/alerted_errors.py
import os
from datetime import date
from typing import Iterable, Set

from .connection import get_cursor

# Scope de alertas: separa la "memoria" de errores por perfil/grupo de destinatarios
# Ejemplos en .env:
#   ALERT_SCOPE=matias_t4app
#   ALERT_SCOPE=matias_gmail
ALERT_SCOPE = os.getenv("ALERT_SCOPE", "default")


def init_db() -> None:
    """
    Crea / migra la tabla de errores avisados si no existe.
    Incluye la columna alert_scope para separar por perfil de alertas.
    """
    with get_cursor() as cur:
        # 1) Crear tabla si no existe (ya con alert_scope)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS alerted_errors (
                id SERIAL PRIMARY KEY,
                app_key     TEXT NOT NULL,
                fecha       DATE NOT NULL,
                tipo        TEXT NOT NULL,        -- 'controlado' / 'no_controlado'
                signature   TEXT NOT NULL,
                alert_scope TEXT NOT NULL DEFAULT 'default',
                first_seen_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """
        )

        # 2) Asegurar que la columna alert_scope existe (por si la tabla es antigua)
        cur.execute(
            """
            ALTER TABLE alerted_errors
            ADD COLUMN IF NOT EXISTS alert_scope TEXT NOT NULL DEFAULT 'default';
            """
        )

        # 3) Quitar la vieja UNIQUE (app_key, fecha, tipo, signature) si existe
        #    (nombre por defecto generado por Postgres)
        cur.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM   pg_constraint
                    WHERE  conname = 'alerted_errors_app_key_fecha_tipo_signature_key'
                    AND    conrelid = 'alerted_errors'::regclass
                ) THEN
                    ALTER TABLE alerted_errors
                    DROP CONSTRAINT alerted_errors_app_key_fecha_tipo_signature_key;
                END IF;
            END$$;
            """
        )

        # 4) Crear UNIQUE nueva incluyendo alert_scope (idempotente)
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM   pg_constraint
                    WHERE  conname = 'alerted_errors_unique_per_scope'
                    AND    conrelid = 'alerted_errors'::regclass
                ) THEN
                    ALTER TABLE alerted_errors
                    ADD CONSTRAINT alerted_errors_unique_per_scope
                    UNIQUE (app_key, fecha, tipo, signature, alert_scope);
                END IF;
            END$$;
            """
        )


def get_alerted_signatures(
    app_key: str,
    fecha: date,
    tipo: str,
) -> Set[str]:
    """
    Devuelve las firmas de errores que ya fueron avisados
    para esa app + fecha + tipo + alert_scope.
    Es decir, la "memoria" es por perfil de alertas (ALERT_SCOPE).
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT signature
            FROM alerted_errors
            WHERE app_key     = %s
              AND fecha       = %s
              AND tipo        = %s
              AND alert_scope = %s
            """,
            (app_key, fecha, tipo, ALERT_SCOPE),
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
    Marca en BD esas firmas como ya avisadas para el ALERT_SCOPE actual.
    Idempotente gracias al UNIQUE (app_key, fecha, tipo, signature, alert_scope).
    """
    signatures = list(signatures)
    if not signatures:
        return

    with get_cursor() as cur:
        for sig in signatures:
            cur.execute(
                """
                INSERT INTO alerted_errors (app_key, fecha, tipo, signature, alert_scope)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (app_key, fecha, tipo, signature, alert_scope) DO NOTHING;
                """,
                (app_key, fecha, tipo, sig, ALERT_SCOPE),
            )


def reset_all_alerted_errors() -> None:
    """
    Borra TODOS los registros de alerted_errors (todos los scopes).
    Útil para forzar que TODO se considere 'nuevo' otra vez.
    """
    with get_cursor() as cur:
        cur.execute("TRUNCATE TABLE alerted_errors;")


def reset_alerted_errors_for_date(fecha: date) -> None:
    """
    Borra todos los registros de alerted_errors para una fecha específica
    (para todos los scopes).
    """
    with get_cursor() as cur:
        cur.execute("DELETE FROM alerted_errors WHERE fecha = %s;", (fecha,))
