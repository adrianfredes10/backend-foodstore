-- migracion 009: tabla refresh_token (B-01)
-- idempotente: CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS refresh_token (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER NOT NULL REFERENCES usuario(id),
    token_hash  VARCHAR(64) UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_refresh_token_usuario_id ON refresh_token (usuario_id);
