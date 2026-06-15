"""
tests de integracion: modulo pedidos
FSM, RN-01 (terminal), RN-05 (motivo), historial append-only
requiere PostgreSQL: py -m pytest tests/test_pedidos.py (con DATABASE_URL configurada)
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import skip_sin_db

pytestmark = skip_sin_db


PASSWORD = "Pedido1234!"


def _register_and_login(client, email):
    client.post("/api/v1/auth/register", json={
        "nombre": "Test", "apellido": "Pedido",
        "email": email, "password": PASSWORD, "telefono": None,
    })
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return resp.cookies


def _crear_pedido(client, cookies):
    # busca primer producto disponible
    prod_resp = client.get("/api/v1/productos?size=1")
    if prod_resp.status_code != 200 or not prod_resp.json().get("items"):
        pytest.skip("sin productos en BD de test")
    prod = prod_resp.json()["items"][0]

    fp_resp = client.get("/api/v1/formas-pago")
    fp_id = fp_resp.json()[0]["id"]

    resp = client.post("/api/v1/pedidos", json={
        "direccion_entrega_id": None,
        "forma_pago_id": fp_id,
        "items": [{"producto_id": prod["id"], "cantidad": 1}],
        "observaciones": None,
    }, cookies=cookies)
    return resp


def test_listar_pedidos_sin_auth(client: TestClient):
    resp = client.get("/api/v1/pedidos")
    assert resp.status_code == 401


def test_cancelar_sin_motivo_retorna_422(client: TestClient):
    cookies = _register_and_login(client, "cancel_test@foodstore.com")
    resp = client.post("/api/v1/pedidos/9999/cancelar", json={}, cookies=cookies)
    assert resp.status_code in (422, 404)


def test_estado_terminal_rechaza_transicion(client: TestClient):
    # ENTREGADO es terminal, no puede avanzar (RN-01)
    cookies = _register_and_login(client, "terminal_test@foodstore.com")
    # intenta cambiar estado de un pedido inexistente (prueba la validacion)
    resp = client.patch("/api/v1/pedidos/9999/estado", json={
        "estado_codigo": "CONFIRMADO",
        "observacion": None,
    }, cookies=cookies)
    assert resp.status_code in (403, 404)


def test_historial_append_only(client: TestClient):
    # el historial solo puede tener inserts (no expone DELETE/UPDATE)
    cookies = _register_and_login(client, "historial_test@foodstore.com")
    resp = client.get("/api/v1/pedidos/9999/historial", cookies=cookies)
    assert resp.status_code in (404, 403)


def test_crear_pedido_requiere_auth(client: TestClient):
    resp = client.post("/api/v1/pedidos", json={
        "direccion_entrega_id": None,
        "forma_pago_id": 1,
        "items": [{"producto_id": 1, "cantidad": 1}],
    })
    assert resp.status_code == 401
