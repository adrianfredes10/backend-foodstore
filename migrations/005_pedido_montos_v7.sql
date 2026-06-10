-- migracion 005: montos v7 en pedido (subtotal, descuento, costo_envio)
-- ejecutar contra la base ANTES de reiniciar el servidor
-- idempotente: usa IF NOT EXISTS y solo puebla filas sin valor

-- ============================================================
-- tabla pedido: nuevos campos de montos
-- ============================================================
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS subtotal    NUMERIC(12,2) DEFAULT 0;
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS descuento   NUMERIC(12,2) DEFAULT 0;
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS costo_envio NUMERIC(12,2) DEFAULT 0;

-- poblar subtotal de pedidos viejos desde la suma de sus detalles
-- (el total historico ya era esa suma: no se les cobraba envio)
UPDATE pedido p SET subtotal = COALESCE((
    SELECT SUM(d.subtotal) FROM detalle_pedido d WHERE d.pedido_id = p.id
), 0)
WHERE p.subtotal IS NULL OR p.subtotal = 0;

-- filas viejas: sin descuento ni envio, total queda intacto
UPDATE pedido SET descuento   = 0 WHERE descuento   IS NULL;
UPDATE pedido SET costo_envio = 0 WHERE costo_envio IS NULL;
