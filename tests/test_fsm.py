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
        event="pedido_cancelado",
    )
    assert ev["event"] == "pedido_cancelado"
    assert ev["pedido_id"] == 1
    assert ev["motivo"] == "sin stock"
    # payload plano: las claves van al nivel raiz, no anidadas en "data"
    assert "data" not in ev
    assert "timestamp" in ev


def test_evento_creacion_sin_estado_anterior():
    ev = _armar_evento(
        pedido_id=2,
        estado_anterior=None,
        estado_nuevo=EstadoPedidoCodigo.PENDIENTE,
        usuario_id=3,
        motivo=None,
    )
    assert ev["estado_anterior"] is None
    assert ev["estado_nuevo"] == EstadoPedidoCodigo.PENDIENTE
    assert ev["event"] == "estado_cambiado"
