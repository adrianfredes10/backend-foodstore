-- migracion 012: tabla pago (MercadoPago, spec v7 / D-03)
-- idempotente: CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS pago (
    id                  SERIAL PRIMARY KEY,
    pedido_id           INTEGER NOT NULL REFERENCES pedido(id),
    idempotency_key     VARCHAR(36) UNIQUE NOT NULL,
    mp_payment_id       VARCHAR(100),
    mp_preference_id    VARCHAR(100),
    mp_status           VARCHAR(50) NOT NULL DEFAULT 'pending',
    mp_status_detail    VARCHAR(100),
    transaction_amount  NUMERIC(12,2) NOT NULL DEFAULT 0,
    currency_id         VARCHAR(10) NOT NULL DEFAULT 'ARS',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_pago_pedido_id ON pago (pedido_id);
