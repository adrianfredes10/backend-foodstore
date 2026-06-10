-- migracion 011: array de imagenes en producto (spec v7 imagenes_url: list)
-- idempotente: ADD COLUMN IF NOT EXISTS

ALTER TABLE producto ADD COLUMN IF NOT EXISTS imagenes_data JSONB;

-- inicializar como array vacio en filas existentes
UPDATE producto SET imagenes_data = '[]' WHERE imagenes_data IS NULL;
