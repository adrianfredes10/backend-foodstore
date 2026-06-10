-- migracion 006: entidad UnidadMedida v7 + FK opcional en ingrediente
-- ejecutar contra la base ANTES de reiniciar el servidor
-- idempotente: CREATE TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS

-- ============================================================
-- nueva tabla unidad_medida
-- ============================================================
CREATE TABLE IF NOT EXISTS unidad_medida (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(50) UNIQUE NOT NULL,
    simbolo VARCHAR(10) UNIQUE NOT NULL,
    tipo    VARCHAR(20) NOT NULL
);

-- ============================================================
-- ingrediente: FK opcional a unidad_medida (D-02)
-- se mantiene la columna string unidad_medida por compatibilidad
-- ============================================================
ALTER TABLE ingrediente
    ADD COLUMN IF NOT EXISTS unidad_medida_id INTEGER REFERENCES unidad_medida(id);
