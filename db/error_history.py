import hashlib
from datetime import datetime
from .connection import get_cursor

def init_error_history_db() -> None:
    """
    Crea la tabla error_history si no existe.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS error_history (
                id SERIAL PRIMARY KEY,
                web_name VARCHAR(255) NOT NULL,
                error_content TEXT NOT NULL,
                error_hash VARCHAR(64) UNIQUE NOT NULL,
                first_seen TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """
        )

def insert_error_history(web_name: str, error_content: str, timestamp: datetime = None) -> None:
    """
    Calcula el hash del error e intenta insertarlo.
    Si el hash ya existe (error duplicado), no hace nada.
    param timestamp: Fecha real de ocurrencia del error. Si es None, usa NOW().
    """
    # Generar Hash SHA-256 único para (web + contenido)
    # Así distinguimos el mismo error en webs distintas si fuera necesario,
    # aunque 'web_name' ya es parte del input.
    unique_string = f"{web_name}:{error_content}"
    error_hash = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

    with get_cursor() as cur:
        if timestamp:
            cur.execute(
                """
                INSERT INTO error_history (web_name, error_content, error_hash, first_seen)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (error_hash) DO NOTHING;
                """,
                (web_name, error_content, error_hash, timestamp)
            )
        else:
            cur.execute(
                """
                INSERT INTO error_history (web_name, error_content, error_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (error_hash) DO NOTHING;
                """,
                (web_name, error_content, error_hash)
            )

def get_error_history(limit: int = 100, offset: int = 0) -> list:
    """
    Obtiene los errores históricos ordenados por fecha desc (más recientes primero).
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, web_name, error_content, first_seen
            FROM error_history
            ORDER BY first_seen DESC
            LIMIT %s OFFSET %s;
            """,
            (limit, offset)
        )
        rows = cur.fetchall()
        
    return [
        {
            "id": row[0],
            "app_name": row[1],
            "error_content": row[2],
            "first_seen": row[3],
        }
        for row in rows
    ]
