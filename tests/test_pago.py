# tests del modulo de pagos (logica pura, sin red ni base de datos)
from app.services.pago_service import _estado_contrato


def test_estado_contrato_approved():
    assert _estado_contrato("approved") == "aprobado"


def test_estado_contrato_rechazos():
    assert _estado_contrato("rejected") == "rechazado"
    assert _estado_contrato("cancelled") == "rechazado"


def test_estado_contrato_pendientes():
    # cualquier estado no terminal de MP se reporta como pendiente
    assert _estado_contrato("pending") == "pendiente"
    assert _estado_contrato("in_process") == "pendiente"
    assert _estado_contrato(None) == "pendiente"


def test_redirect_status_validos():
    from app.routers.v1.pagos import REDIRECT_STATUS_VALIDOS

    assert REDIRECT_STATUS_VALIDOS == {"success", "failure", "pending"}
