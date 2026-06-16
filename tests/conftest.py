"""
fixtures para tests de integracion con TestClient.

Requiere PostgreSQL: correr con DATABASE_URL=postgresql://...  (idealmente una
base de TEST dedicada). Sin Postgres, los tests de integracion se saltan solos.

    DATABASE_URL="postgresql://postgres:1234postgres@localhost:5434/parcial_prog4_test" \\
        py -m pytest -q --cov=app --cov-report=term
"""
import os

# Rate limit OFF en tests: el bucket es por-IP y todos los tests salen de la
# misma IP del TestClient -> tras 5 logins da 429 y rompe auth en cascada.
# Debe setearse ANTES de importar la app (get_settings se cachea al crear el
# middleware de rate limit).
os.environ.setdefault("RATE_LIMIT_AUTH_MAX", "100000")

import pytest
from fastapi.testclient import TestClient


def _pg_disponible() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith("postgresql")


# skip silencioso si no hay postgres configurado
skip_sin_db = pytest.mark.skipif(
    not _pg_disponible(),
    reason="requiere DATABASE_URL=postgresql://...",
)


@pytest.fixture(scope="session", autouse=True)
def _reset_db():
    # Base limpia por sesion: dropea + recrea + re-seedea, para que la suite sea
    # reproducible (sin esto, datos de corridas previas rompen tests idempotentes
    # como register de un email ya existente).
    if not _pg_disponible():
        yield
        return
    import app.models  # noqa: F401  registra los modelos en SQLModel.metadata
    from sqlmodel import SQLModel
    from app.database import engine
    from app.seed_obligatorio import run_seed_obligatorio

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    run_seed_obligatorio()
    yield


@pytest.fixture(name="client")
def client_fixture():
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(name="admin_cookies")
def admin_cookies_fixture(client):
    client.post("/api/v1/auth/register", json={
        "nombre": "Admin", "apellido": "Test",
        "email": "admin_int@foodstore.com", "password": "Admin1234!",
        "telefono": None,
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin_int@foodstore.com", "password": "Admin1234!",
    })
    return resp.cookies


@pytest.fixture(name="client_cookies")
def client_cookies_fixture(client):
    client.post("/api/v1/auth/register", json={
        "nombre": "Cliente", "apellido": "Test",
        "email": "cliente_int@foodstore.com", "password": "Cliente1234!",
        "telefono": None,
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "cliente_int@foodstore.com", "password": "Cliente1234!",
    })
    return resp.cookies
