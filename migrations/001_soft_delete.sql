-- Borrado lógico: columnas + índices únicos parciales (solo filas activas).
-- Ejecutar una vez contra la base del proyecto (ej. parcial_prog4 en localhost:5434).

ALTER TABLE categoria   ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE producto    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Categoria
ALTER TABLE categoria DROP CONSTRAINT IF EXISTS categoria_nombre_key;
DROP INDEX IF EXISTS ix_categoria_nombre;
CREATE UNIQUE INDEX IF NOT EXISTS uq_categoria_nombre_activo
    ON categoria (nombre) WHERE deleted_at IS NULL;

-- Ingrediente
ALTER TABLE ingrediente DROP CONSTRAINT IF EXISTS ingrediente_nombre_key;
DROP INDEX IF EXISTS ix_ingrediente_nombre;
CREATE UNIQUE INDEX IF NOT EXISTS uq_ingrediente_nombre_activo
    ON ingrediente (nombre) WHERE deleted_at IS NULL;

-- Producto
ALTER TABLE producto DROP CONSTRAINT IF EXISTS producto_nombre_key;
DROP INDEX IF EXISTS ix_producto_nombre;
CREATE UNIQUE INDEX IF NOT EXISTS uq_producto_nombre_activo
    ON producto (nombre) WHERE deleted_at IS NULL;
