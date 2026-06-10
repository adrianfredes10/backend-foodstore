-- migracion 007: imagen_url en categoria (v7, Cloudinary)
-- idempotente: ADD COLUMN IF NOT EXISTS

ALTER TABLE categoria ADD COLUMN IF NOT EXISTS imagen_url VARCHAR(500);
