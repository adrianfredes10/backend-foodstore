-- migración parcial 2: alineación del modelo con la documentación técnica
-- ejecutar contra la base ANTES de reiniciar el servidor
-- idempotente: cada ALTER usa IF NOT EXISTS / IF EXISTS donde aplica

-- ============================================================
-- tabla usuario: nuevos campos de perfil + activo
-- ============================================================
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS nombre     VARCHAR(120);
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS apellido   VARCHAR(120);
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS telefono   VARCHAR(30);
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS activo     BOOLEAN DEFAULT TRUE;

-- poblar activo desde disabled (si la columna disabled existe)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'usuario' AND column_name = 'disabled'
    ) THEN
        UPDATE usuario SET activo = NOT disabled WHERE activo IS NULL;
    END IF;
END $$;

UPDATE usuario SET activo = TRUE WHERE activo IS NULL;
UPDATE usuario SET nombre  = '' WHERE nombre  IS NULL;
UPDATE usuario SET apellido = '' WHERE apellido IS NULL;

-- ============================================================
-- tabla usuario_rol: fecha de asignación
-- ============================================================
ALTER TABLE usuario_rol ADD COLUMN IF NOT EXISTS fecha_asignacion TIMESTAMPTZ DEFAULT NOW();

-- ============================================================
-- tabla ingrediente: descripcion y flag alergeno global
-- ============================================================
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS descripcion  VARCHAR(500);
ALTER TABLE ingrediente ADD COLUMN IF NOT EXISTS es_alergeno  BOOLEAN DEFAULT FALSE;

-- ============================================================
-- tabla categoria: flag activa
-- ============================================================
ALTER TABLE categoria ADD COLUMN IF NOT EXISTS activa BOOLEAN DEFAULT TRUE;
UPDATE categoria SET activa = TRUE WHERE activa IS NULL;

-- ============================================================
-- tabla producto: imagen_url + categoria_id (1:N)
-- ============================================================
ALTER TABLE producto ADD COLUMN IF NOT EXISTS imagen_url   VARCHAR(500);
ALTER TABLE producto ADD COLUMN IF NOT EXISTS categoria_id INTEGER REFERENCES categoria(id);

-- poblar categoria_id desde la tabla producto_categoria (toma la primera relación)
UPDATE producto p
SET categoria_id = (
    SELECT pc.categoria_id
    FROM producto_categoria pc
    WHERE pc.producto_id = p.id
    ORDER BY pc.categoria_id
    LIMIT 1
)
WHERE p.categoria_id IS NULL;

-- nota: la tabla producto_categoria se puede eliminar después de verificar
-- que todos los productos tienen categoria_id asignado. No se elimina acá
-- para no perder datos si la migración se ejecuta por primera vez.

-- ============================================================
-- tabla estado_pedido: orden de visualización
-- ============================================================
ALTER TABLE estado_pedido ADD COLUMN IF NOT EXISTS orden INTEGER DEFAULT 0;
UPDATE estado_pedido SET orden = CASE codigo
    WHEN 'PENDIENTE'   THEN 1
    WHEN 'CONFIRMADO'  THEN 2
    WHEN 'EN_PREP'     THEN 3
    WHEN 'EN_CAMINO'   THEN 4
    WHEN 'ENTREGADO'   THEN 5
    WHEN 'CANCELADO'   THEN 6
    ELSE 0
END;

-- ============================================================
-- tabla forma_pago: flag activa
-- ============================================================
ALTER TABLE forma_pago ADD COLUMN IF NOT EXISTS activa BOOLEAN DEFAULT TRUE;
UPDATE forma_pago SET activa = TRUE WHERE activa IS NULL;

-- ============================================================
-- tabla pedido: renombrar FK de estado + nuevos campos
-- ============================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'pedido' AND column_name = 'estado_pedido_id'
    ) THEN
        ALTER TABLE pedido RENAME COLUMN estado_pedido_id TO estado_id;
    END IF;
END $$;

ALTER TABLE pedido ADD COLUMN IF NOT EXISTS observaciones       VARCHAR(500);
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS fecha_confirmacion  TIMESTAMPTZ;
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS fecha_entrega       TIMESTAMPTZ;

-- ============================================================
-- tabla detalle_pedido: renombrar snapshots + subtotal
-- ============================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'detalle_pedido' AND column_name = 'nombre_producto_snapshot'
    ) THEN
        ALTER TABLE detalle_pedido RENAME COLUMN nombre_producto_snapshot TO producto_nombre;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'detalle_pedido' AND column_name = 'precio_unit_snapshot'
    ) THEN
        ALTER TABLE detalle_pedido RENAME COLUMN precio_unit_snapshot TO precio_unitario;
    END IF;
END $$;

ALTER TABLE detalle_pedido ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2) DEFAULT 0;
UPDATE detalle_pedido SET subtotal = precio_unitario * cantidad WHERE subtotal = 0;

-- ============================================================
-- tabla historial_estado_pedido: renombrar created_at + observacion
-- ============================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'historial_estado_pedido' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE historial_estado_pedido RENAME COLUMN created_at TO fecha;
    END IF;
END $$;

ALTER TABLE historial_estado_pedido ADD COLUMN IF NOT EXISTS observacion VARCHAR(500);

-- ============================================================
-- tabla direccion_entrega: separar linea_direccion en calle/numero/referencia
-- ============================================================
ALTER TABLE direccion_entrega ADD COLUMN IF NOT EXISTS calle      VARCHAR(200);
ALTER TABLE direccion_entrega ADD COLUMN IF NOT EXISTS numero     VARCHAR(20);
ALTER TABLE direccion_entrega ADD COLUMN IF NOT EXISTS referencia VARCHAR(300);

-- poblar calle desde linea_direccion si existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'direccion_entrega' AND column_name = 'linea_direccion'
    ) THEN
        UPDATE direccion_entrega SET calle = linea_direccion WHERE calle IS NULL;
    END IF;
END $$;

UPDATE direccion_entrega SET calle  = 'Sin especificar' WHERE calle  IS NULL;
UPDATE direccion_entrega SET numero = 'S/N'              WHERE numero IS NULL;
