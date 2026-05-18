-- Jerarquía de categorías (self-FK) + deleted_at por compatibilidad si faltara

ALTER TABLE categoria ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES categoria (id);
ALTER TABLE categoria ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
