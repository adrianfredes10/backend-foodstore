-- migracion v7: campos faltantes, renombres de columnas

-- celular en usuario (v7)
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS celular VARCHAR(20);

-- unidad_venta_id en producto (v7)
ALTER TABLE producto ADD COLUMN IF NOT EXISTS unidad_venta_id BIGINT REFERENCES unidad_medida(id);

-- personalizacion en detalle_pedido (IDs de ingredientes removidos)
ALTER TABLE detalle_pedido ADD COLUMN IF NOT EXISTS personalizacion INTEGER[];

-- renombrar columnas detalle_pedido para alinearse a spec v6/v7
ALTER TABLE detalle_pedido RENAME COLUMN producto_nombre TO nombre_snapshot;
ALTER TABLE detalle_pedido RENAME COLUMN precio_unitario TO precio_snapshot;
ALTER TABLE detalle_pedido RENAME COLUMN subtotal TO subtotal_snap;

-- renombrar columnas historial_estado_pedido
ALTER TABLE historial_estado_pedido RENAME COLUMN fecha TO created_at;
ALTER TABLE historial_estado_pedido RENAME COLUMN observacion TO motivo;

-- campos faltantes en producto_ingrediente (v7)
ALTER TABLE producto_ingrediente ADD COLUMN IF NOT EXISTS es_removible BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE producto_ingrediente ADD COLUMN IF NOT EXISTS unidad_medida_id BIGINT REFERENCES unidad_medida(id);
