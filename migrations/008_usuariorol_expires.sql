-- migracion 008: expires_at en usuario_rol (v7, D-05)
-- idempotente: ADD COLUMN IF NOT EXISTS

ALTER TABLE usuario_rol ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
