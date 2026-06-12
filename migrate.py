# aplica las migraciones a una base existente (idempotente, se puede re-correr)
# uso: python migrate.py
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234postgres@localhost:5434/parcial_prog4",
)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 001-003 (los .sql originales ya no estan en el repo; quedan inline)
cur.execute("ALTER TABLE categoria ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES categoria(id);")
cur.execute("ALTER TABLE categoria ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")
cur.execute("ALTER TABLE producto ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")
cur.execute("ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")
conn.commit()
print("[ok] migraciones base (001-003)")

# 004 en adelante: archivos .sql en orden
for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
    sql = sql_file.read_text(encoding="utf-8")
    try:
        cur.execute(sql)
        conn.commit()
        print(f"[ok] {sql_file.name}")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] {sql_file.name}: {e}")
        raise

cur.close()
conn.close()
print("Migración completada.")
