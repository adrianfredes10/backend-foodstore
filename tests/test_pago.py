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


# --- integracion: un pago aprobado DEBE confirmar el pedido ---
import asyncio
import uuid

from sqlmodel import select

from tests.conftest import skip_sin_db


class _FakePaymentApi:
    def __init__(self, resp):
        self._resp = resp

    def get(self, _payment_id):
        return self._resp


class _FakeSDK:
    def __init__(self, resp):
        self._resp = resp

    def payment(self):
        return _FakePaymentApi(self._resp)


@skip_sin_db
def test_pago_aprobado_confirma_pedido(monkeypatch):
    # regresion: antes _sincronizar_payment llamaba cambiar_estado(observacion=...)
    # cuando el parametro es `motivo` -> TypeError silencioso -> el pedido nunca
    # pasaba de PENDIENTE a CONFIRMADO aunque MP aprobara el pago.
    from app.uow import UnitOfWork
    from app.models.pedido import EstadoPedido, FormaPago, Pedido
    from app.models.pago import Pago
    from app.models.seguridad import Usuario
    from app.models.direccion_entrega import DireccionEntrega
    from app.constants.codigos import EstadoPedidoCodigo, FormaPagoCodigo
    from app.services import pago_service as pago_mod
    from app.services.pago_service import PagoService

    # arrange: pedido PENDIENTE con MercadoPago + pago pendiente (datos del seed)
    with UnitOfWork() as uow:
        cli = uow.session.exec(
            select(Usuario).where(Usuario.email == "cliente@foodstore.local")
        ).first()
        dire = uow.session.exec(
            select(DireccionEntrega).where(DireccionEntrega.usuario_id == cli.id)
        ).first()
        est_pend = uow.session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == EstadoPedidoCodigo.PENDIENTE)
        ).first()
        forma_mp = uow.session.exec(
            select(FormaPago).where(FormaPago.codigo == FormaPagoCodigo.MERCADOPAGO)
        ).first()
        pedido = Pedido(
            usuario_id=cli.id,
            direccion_entrega_id=dire.id,
            forma_pago_id=forma_mp.id,
            estado_id=est_pend.id,
            subtotal=100, descuento=0, costo_envio=0, total=100,
        )
        uow.pedidos.create_pedido(pedido)
        pedido_id = pedido.id
        uow.pagos.add(Pago(
            pedido_id=pedido_id,
            idempotency_key=str(uuid.uuid4()),
            mp_status="pending",
            transaction_amount=100,
            currency_id="ARS",
            external_reference=str(pedido_id),
        ))

    # mock: MP responde que el pago esta aprobado
    fake_resp = {
        "status": 200,
        "response": {
            "id": 999999,
            "status": "approved",
            "status_detail": "accredited",
            "external_reference": str(pedido_id),
            "transaction_amount": 100.0,
            "payment_method_id": "visa",
        },
    }
    monkeypatch.setattr(pago_mod, "esta_configurado", lambda: True)
    monkeypatch.setattr(pago_mod, "get_sdk", lambda: _FakeSDK(fake_resp))

    # act: llega el webhook de MP
    asyncio.run(PagoService(UnitOfWork()).procesar_webhook("999999"))

    # assert: el pedido quedo CONFIRMADO
    with UnitOfWork() as uow:
        p = uow.pedidos.get_pedido(pedido_id)
        est = uow.session.exec(
            select(EstadoPedido).where(EstadoPedido.id == p.estado_id)
        ).first()
    assert est.codigo == EstadoPedidoCodigo.CONFIRMADO
