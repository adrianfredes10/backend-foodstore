-- migracion 010: public_id de Cloudinary en producto (modulo /uploads)
-- idempotente: ADD COLUMN IF NOT EXISTS

ALTER TABLE producto ADD COLUMN IF NOT EXISTS imagen_public_id VARCHAR(255);
