# db/connection.py
import os
from contextlib import contextmanager

import psycopg2


def get_connection():
    """
    Crea una conexión a Postgres usando variables de entorno:
    PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE.
    """
    return psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", 5432)),
    dbname=os.getenv("PGDATABASE", "logs_db"),
    user=os.getenv("PGUSER", "postgres"),      # <- default postgres
    password=os.getenv("PGPASSWORD", "logs_password"),
)



@contextmanager
def get_cursor():
    """
    Context manager que entrega un cursor y hace commit al final.
    Cierra la conexión automáticamente.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()
