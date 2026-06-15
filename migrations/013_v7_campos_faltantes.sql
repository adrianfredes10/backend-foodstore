-- migracion v7: campos nuevos unicamente (sin renombres para compatibilidad con frontends)

-- celular en usuario (v7)
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS celular VARCHAR(20);

-- unidad_venta_id en producto (v7)
ALTER TABLE producto ADD COLUMN IF NOT EXISTS unidad_venta_id BIGINT REFERENCES unidad_medida(id);

-- personalizacion en detalle_pedido (IDs de ingredientes removidos)
ALTER TABLE detalle_pedido ADD COLUMN IF NOT EXISTS personalizacion INTEGER[];

-- campos nuevos en producto_ingrediente (v7)
ALTER TABLE producto_ingrediente ADD COLUMN IF NOT EXISTS es_removible BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE producto_ingrediente ADD COLUMN IF NOT EXISTS unidad_medida_id BIGINT REFERENCES unidad_medida(id);
