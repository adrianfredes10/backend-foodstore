-- migracion 012: tabla pago (MercadoPago, spec v7 / D-03)
-- idempotente: CREATE TABLE IF NOT EXISTS + ALTER ADD COLUMN IF NOT EXISTS

CREATE TABLE IF NOT EXISTS pago (
    id                  SERIAL PRIMARY KEY,
    pedido_id           INTEGER NOT NULL REFERENCES pedido(id),
    idempotency_key     VARCHAR(36) UNIQUE NOT NULL,
    mp_payment_id       VARCHAR(100),
    mp_preference_id    VARCHAR(100),
    mp_status           VARCHAR(50) NOT NULL DEFAULT 'pending',
    mp_status_detail    VARCHAR(100),
    payment_method_id   VARCHAR(50),
    external_reference  VARCHAR(100),
    transaction_amount  NUMERIC(12,2) NOT NULL DEFAULT 0,
    currency_id         VARCHAR(10) NOT NULL DEFAULT 'ARS',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- por si la tabla ya existia sin estos campos (spec v7 §3.3: Pago completo)
ALTER TABLE pago ADD COLUMN IF NOT EXISTS payment_method_id  VARCHAR(50);
ALTER TABLE pago ADD COLUMN IF NOT EXISTS external_reference VARCHAR(100);

CREATE INDEX IF NOT EXISTS ix_pago_pedido_id ON pago (pedido_id);
CREATE INDEX IF NOT EXISTS ix_pago_external_reference ON pago (external_reference);
