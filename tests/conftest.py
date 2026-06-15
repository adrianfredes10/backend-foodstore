"""
fixtures para tests de integracion con TestClient
requiere PostgreSQL disponible (DATABASE_URL en .env)
los tests de integracion se marcan con @pytest.mark.integration
para correrlos: py -m pytest tests/ -m integration
para solo unit tests: py -m pytest tests/ -m "not integration"
"""
import os
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
