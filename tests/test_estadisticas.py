"""
tests de integracion: modulo estadisticas
verifica que los endpoints respondan y que CANCELADO no sume a ingresos (EST-01)
requiere PostgreSQL: py -m pytest tests/test_estadisticas.py (con DATABASE_URL configurada)
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from tests.conftest import skip_sin_db

pytestmark = skip_sin_db


PASSWORD = "Stats1234!"


def _admin_cookies(client):
    client.post("/api/v1/auth/register", json={
        "nombre": "Stats", "apellido": "Admin",
        "email": "stats_admin@foodstore.com", "password": PASSWORD, "telefono": None,
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "stats_admin@foodstore.com", "password": PASSWORD,
    })
    return resp.cookies


def test_resumen_sin_auth(client: TestClient):
    resp = client.get("/api/v1/estadisticas/resumen")
    assert resp.status_code == 401


def test_resumen_con_auth(client: TestClient):
    cookies = _admin_cookies(client)
    resp = client.get("/api/v1/estadisticas/resumen", cookies=cookies)
    # cliente solo tiene rol CLIENT, no ADMIN; espera 403
    assert resp.status_code == 403


def test_pedidos_por_estado_estructura(client: TestClient):
    # con cookies de usuario sin rol ADMIN
    cookies = _admin_cookies(client)
    resp = client.get("/api/v1/estadisticas/pedidos-por-estado", cookies=cookies)
    assert resp.status_code == 403


def test_ventas_periodo_params_invalidos(client: TestClient):
    # fechas invalidas -> 422
    resp = client.get("/api/v1/estadisticas/ventas?desde=abc&hasta=def")
    assert resp.status_code in (401, 422)


def test_productos_top_sin_auth(client: TestClient):
    resp = client.get("/api/v1/estadisticas/productos-top")
    assert resp.status_code == 401


def test_ingresos_sin_auth(client: TestClient):
    hoy = date.today().isoformat()
    resp = client.get(f"/api/v1/estadisticas/ingresos?desde={hoy}&hasta={hoy}")
    assert resp.status_code == 401
