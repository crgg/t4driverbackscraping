# debug_db.py
import os
import psycopg2
from dotenv import load_dotenv   # ⬅️ nuevo

load_dotenv()                    # ⬅️ nuevo

print("PGHOST =", os.getenv("PGHOST"))
print("PGPORT =", os.getenv("PGPORT"))
print("PGUSER =", os.getenv("PGUSER"))
print("PGDATABASE =", os.getenv("PGDATABASE"))

conn = psycopg2.connect(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", 5433)),
    dbname=os.getenv("PGDATABASE", "postgres"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", "logs_password"),
)
cur = conn.cursor()

cur.execute("SELECT current_database(), current_user;")
print("DB y usuario reales:", cur.fetchone())

cur.execute("SELECT inet_server_addr()::text, inet_server_port();")
print("Servidor real:", cur.fetchone())

# Probamos la tabla
try:
    cur.execute("SELECT count(*) FROM alerted_errors;")
    print("alerted_errors.count =", cur.fetchone()[0])
except psycopg2.Error as e:
    print("Error al consultar alerted_errors:", e)

cur.close()
conn.close()
