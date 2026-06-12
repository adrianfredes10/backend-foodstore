# tests de la FSM de pedidos (logica pura, sin base de datos)
from app.constants.codigos import EstadoPedidoCodigo
from app.services.pedido_service import TRANSICIONES, _armar_evento


def test_transiciones_desde_pendiente():
    permitidos = TRANSICIONES[EstadoPedidoCodigo.PENDIENTE]
    assert EstadoPedidoCodigo.CONFIRMADO in permitidos
    assert EstadoPedidoCodigo.CANCELADO in permitidos
    assert EstadoPedidoCodigo.EN_PREP not in permitidos


def test_transiciones_desde_confirmado():
    permitidos = TRANSICIONES[EstadoPedidoCodigo.CONFIRMADO]
    assert permitidos == [EstadoPedidoCodigo.EN_PREP, EstadoPedidoCodigo.CANCELADO]


def test_estados_terminales_sin_salida():
    assert TRANSICIONES[EstadoPedidoCodigo.ENTREGADO] == []
    assert TRANSICIONES[EstadoPedidoCodigo.CANCELADO] == []


def test_no_existe_en_camino():
    assert not hasattr(EstadoPedidoCodigo, "EN_CAMINO")
    for destinos in TRANSICIONES.values():
        assert "EN_CAMINO" not in destinos


def test_evento_cancelado_lleva_motivo():
    ev = _armar_evento(
        pedido_id=1,
        estado_anterior=EstadoPedidoCodigo.PENDIENTE,
        estado_nuevo=EstadoPedidoCodigo.CANCELADO,
        usuario_id=7,
        motivo="sin stock",
    )
    # shape del CONTRATO-API: {"event": "PEDIDO_ACTUALIZADO", "data": {...}}
    assert ev["event"] == "PEDIDO_ACTUALIZADO"
    assert ev["data"]["pedido_id"] == 1
    assert ev["data"]["motivo"] == "sin stock"
    assert "timestamp" in ev["data"]


def test_evento_creacion_sin_estado_anterior():
    ev = _armar_evento(
        pedido_id=2,
        estado_anterior=None,
        estado_nuevo=EstadoPedidoCodigo.PENDIENTE,
        usuario_id=3,
        motivo=None,
    )
    assert ev["event"] == "PEDIDO_ACTUALIZADO"
    assert ev["data"]["estado_anterior"] is None
    assert ev["data"]["estado_nuevo"] == EstadoPedidoCodigo.PENDIENTE
