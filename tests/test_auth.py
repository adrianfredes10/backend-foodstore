"""
tests de integracion: modulo auth
register, login, logout, refresh, rate limit
requiere PostgreSQL: py -m pytest tests/test_auth.py (con DATABASE_URL configurada)
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import skip_sin_db

pytestmark = skip_sin_db

EMAIL = "auth_user@foodstore.com"
PASSWORD = "Segura1234!"


def test_register_ok(client: TestClient):
    resp = client.post("/api/v1/auth/register", json={
        "nombre": "Juan",
        "apellido": "Perez",
        "email": EMAIL,
        "password": PASSWORD,
        "telefono": None,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == EMAIL
    assert "password" not in data
    assert "password_hash" not in data


def test_register_email_duplicado(client: TestClient):
    # nombre/apellido validos (min 2 chars); email duplicado -> 409 Conflict
    client.post("/api/v1/auth/register", json={
        "nombre": "Ana", "apellido": "Bravo",
        "email": "dup@foodstore.com", "password": PASSWORD, "telefono": None,
    })
    resp = client.post("/api/v1/auth/register", json={
        "nombre": "Ana", "apellido": "Bravo",
        "email": "dup@foodstore.com", "password": PASSWORD, "telefono": None,
    })
    assert resp.status_code == 409


def test_login_ok(client: TestClient):
    client.post("/api/v1/auth/register", json={
        "nombre": "Login", "apellido": "Test",
        "email": "login_ok@foodstore.com", "password": PASSWORD, "telefono": None,
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "login_ok@foodstore.com",
        "password": PASSWORD,
    })
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


def test_login_credenciales_invalidas(client: TestClient):
    resp = client.post("/api/v1/auth/login", json={
        "email": "noexiste@foodstore.com",
        "password": "Mal1234!",
    })
    assert resp.status_code == 401


def test_me_sin_auth(client: TestClient):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_con_auth(client: TestClient):
    client.post("/api/v1/auth/register", json={
        "nombre": "Me", "apellido": "Test",
        "email": "me_test@foodstore.com", "password": PASSWORD, "telefono": None,
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "me_test@foodstore.com", "password": PASSWORD,
    })
    resp = client.get("/api/v1/auth/me", cookies=login.cookies)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me_test@foodstore.com"


def test_logout_revoca_sesion(client: TestClient):
    client.post("/api/v1/auth/register", json={
        "nombre": "Logout", "apellido": "Test",
        "email": "logout_test@foodstore.com", "password": PASSWORD, "telefono": None,
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "logout_test@foodstore.com", "password": PASSWORD,
    })
    cookies = login.cookies
    logout = client.post("/api/v1/auth/logout", cookies=cookies)
    assert logout.status_code in (200, 204)
    # el access_token es un JWT stateless (vale hasta expirar); lo que el logout
    # garantiza es revocar el REFRESH -> no se puede renovar la sesion.
    resp = client.post("/api/v1/auth/refresh", cookies=cookies)
    assert resp.status_code == 401


def test_refresh_sin_cookie_retorna_401(client: TestClient):
    resp = client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
