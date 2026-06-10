-- migracion 004: FSM v7 a 5 estados (elimina EN_CAMINO) + es_terminal
-- ejecutar contra la base ANTES de reiniciar el servidor
-- idempotente: se puede correr mas de una vez sin romper
-- NO toca historial_estado_pedido (append-only, RN-03)

-- ============================================================
-- tabla estado_pedido: nueva columna es_terminal
-- ============================================================
ALTER TABLE estado_pedido ADD COLUMN IF NOT EXISTS es_terminal BOOLEAN DEFAULT FALSE;

-- es_terminal y orden segun el codigo (5 estados v7)
UPDATE estado_pedido SET es_terminal = CASE codigo
    WHEN 'ENTREGADO' THEN TRUE
    WHEN 'CANCELADO' THEN TRUE
    ELSE FALSE
END;

UPDATE estado_pedido SET orden = CASE codigo
    WHEN 'PENDIENTE'  THEN 1
    WHEN 'CONFIRMADO' THEN 2
    WHEN 'EN_PREP'    THEN 3
    WHEN 'ENTREGADO'  THEN 4
    WHEN 'CANCELADO'  THEN 5
    ELSE orden
END;

-- ============================================================
-- migrar pedidos que quedaron en EN_CAMINO -> EN_PREP
-- (EN_CAMINO ya no existe en la FSM v7)
-- ============================================================
DO $$
DECLARE
    id_en_camino INTEGER;
    id_en_prep   INTEGER;
    refs_hist    INTEGER;
BEGIN
    SELECT id INTO id_en_camino FROM estado_pedido WHERE codigo = 'EN_CAMINO';
    SELECT id INTO id_en_prep   FROM estado_pedido WHERE codigo = 'EN_PREP';

    IF id_en_camino IS NULL THEN
        RAISE NOTICE 'EN_CAMINO no existe, nada que migrar';
        RETURN;
    END IF;

    -- reasignar pedidos activos a EN_PREP
    IF id_en_prep IS NOT NULL THEN
        UPDATE pedido SET estado_id = id_en_prep WHERE estado_id = id_en_camino;
    END IF;

    -- el historial puede referenciar EN_CAMINO; no se modifica (RN-03)
    SELECT COUNT(*) INTO refs_hist
    FROM historial_estado_pedido
    WHERE estado_anterior_id = id_en_camino
       OR estado_nuevo_id = id_en_camino;

    IF refs_hist = 0 THEN
        DELETE FROM estado_pedido WHERE id = id_en_camino;
        RAISE NOTICE 'EN_CAMINO eliminado de estado_pedido';
    ELSE
        RAISE NOTICE 'EN_CAMINO conservado: % filas de historial lo referencian', refs_hist;
    END IF;
END $$;
