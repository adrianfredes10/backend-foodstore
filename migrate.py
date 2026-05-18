import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234postgres@localhost:5432/parcial_prog4")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("ALTER TABLE categoria ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES categoria(id);")
cur.execute("ALTER TABLE categoria ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")
cur.execute("ALTER TABLE producto ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")
cur.execute("ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;")

conn.commit()
cur.close()
conn.close()
print("Migración completada.")
