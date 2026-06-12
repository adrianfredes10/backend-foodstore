# pagos MercadoPago: create-preference, webhook IPN, confirm manual
# las llamadas al SDK de MP van FUERA del bloque UoW (I/O de red, no transaccion)
# idempotency_key UUID generado aca (ID-01), nunca por el frontend
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.constants.codigos import EstadoPedidoCodigo, FormaPagoCodigo, RolCodigo
from app.core.config import get_settings
from app.core.mercadopago_setup import esta_configurado, get_sdk
from app.models.pago import Pago
from app.schemas.pago_schemas import (
    PagoCrearResponse,
    PagoEstadoResponse,
    PagoRead,
)
from app.services.pedido_service import PedidoService
from app.uow import UnitOfWork

logger = logging.getLogger("app.pagos")

CURRENCY = "ARS"

# mp_status -> estado del contrato ("pendiente" | "aprobado" | "rechazado")
_ESTADO_MAP = {
    "approved": "aprobado",
    "rejected": "rechazado",
    "cancelled": "rechazado",
}


def _estado_contrato(mp_status: Optional[str]) -> str:
    if not mp_status:
        return "pendiente"
    return _ESTADO_MAP.get(mp_status, "pendiente")


class PagoService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        # evento WS si el pago confirmo el pedido; lo emite el router post-commit
        self.evento_ws: Optional[dict] = None

    async def create_preference(
        self, pedido_id: int, usuario_id: int
    ) -> PagoCrearResponse:
        if not esta_configurado():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "MercadoPago no configurado"
            )

        settings = get_settings()

        with self.uow as uow:
            pedido = uow.pedidos.get_pedido(pedido_id)
            if not pedido or pedido.usuario_id != usuario_id:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Pedido no encontrado"
                )
            forma_pago = uow.pedidos.get_forma_pago(pedido.forma_pago_id)
            if not forma_pago or forma_pago.codigo != FormaPagoCodigo.MERCADOPAGO:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "La forma de pago del pedido no es MercadoPago",
                )
            estado = uow.pedidos.get_estado_by_id(pedido.estado_id)
            if estado.codigo != EstadoPedidoCodigo.PENDIENTE:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"El pedido esta en estado '{estado.codigo}', no admite pago",
                )
            ultimo = uow.pagos.get_ultimo_por_pedido(pedido_id)
            if ultimo and ultimo.mp_status == "approved":
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "El pedido ya tiene un pago aprobado"
                )
            total = pedido.total

        idempotency_key = str(uuid.uuid4())
        base = settings.BACKEND_URL.rstrip("/")
        preference_data = {
            "items": [
                {
                    "title": f"Pedido #{pedido_id} - Food Store",
                    "quantity": 1,
                    "unit_price": float(total),
                    "currency_id": CURRENCY,
                }
            ],
            # external_reference enlaza el pago de MP con nuestro pedido
            "external_reference": str(pedido_id),
            "back_urls": {
                "success": f"{base}/api/v1/pagos/redirect/{pedido_id}/success",
                "failure": f"{base}/api/v1/pagos/redirect/{pedido_id}/failure",
                "pending": f"{base}/api/v1/pagos/redirect/{pedido_id}/pending",
            },
            "notification_url": f"{base}/api/v1/pagos/webhook",
        }

        # SDK fuera del UoW
        sdk = get_sdk()
        resp = await asyncio.to_thread(
            sdk.preference().create, preference_data
        )
        body = resp.get("response") or {}
        preference_id = body.get("id")
        if resp.get("status") not in (200, 201) or not preference_id:
            logger.error("error creando preferencia MP: %s", resp)
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "MercadoPago rechazo la creacion de la preferencia",
            )

        with self.uow as uow:
            pago = uow.pagos.add(
                Pago(
                    pedido_id=pedido_id,
                    idempotency_key=idempotency_key,
                    mp_preference_id=preference_id,
                    mp_status="pending",
                    transaction_amount=total,
                    currency_id=CURRENCY,
                )
            )
            pago_id = pago.id

        return PagoCrearResponse(
            pago_id=pago_id,
            preference_id=preference_id,
            init_point=body.get("init_point"),
            public_key=settings.MERCADOPAGO_PUBLIC_KEY or None,
        )

    async def procesar_webhook(self, payment_id: Optional[str]) -> None:
        # nunca lanza: el webhook responde 200 siempre (MP reintenta ante 4xx/5xx)
        if not payment_id or not esta_configurado():
            return
        try:
            await self._sincronizar_payment(str(payment_id))
        except Exception:
            logger.exception("error procesando webhook MP payment_id=%s", payment_id)

    async def confirm(
        self, pedido_id: int, usuario_id: int, payment_id: Optional[int] = None
    ) -> PagoEstadoResponse:
        if not esta_configurado():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "MercadoPago no configurado"
            )

        with self.uow as uow:
            pedido = uow.pedidos.get_pedido(pedido_id)
            if not pedido or pedido.usuario_id != usuario_id:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Pedido no encontrado"
                )
            ultimo = uow.pagos.get_ultimo_por_pedido(pedido_id)

        mp_payment_id: Optional[str] = (
            str(payment_id) if payment_id else (ultimo.mp_payment_id if ultimo else None)
        )

        if not mp_payment_id:
            # el webhook todavia no llego: buscar en MP por external_reference
            sdk = get_sdk()
            resp = await asyncio.to_thread(
                sdk.payment().search, {"external_reference": str(pedido_id)}
            )
            results = (resp.get("response") or {}).get("results") or []
            if results:
                results.sort(key=lambda p: p.get("date_created") or "", reverse=True)
                mp_payment_id = str(results[0].get("id"))

        if not mp_payment_id:
            return PagoEstadoResponse(
                estado=_estado_contrato(ultimo.mp_status if ultimo else None),
                pedido_id=pedido_id,
            )

        mp_status = await self._sincronizar_payment(mp_payment_id)
        return PagoEstadoResponse(
            estado=_estado_contrato(mp_status), pedido_id=pedido_id
        )

    def obtener_por_pedido(
        self, pedido_id: int, usuario_id: int, roles: set[str]
    ) -> PagoRead:
        # lectura para detalle de pedido (cliente dueño o staff)
        with self.uow as uow:
            pedido = uow.pedidos.get_pedido(pedido_id)
            if not pedido:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "Pedido no encontrado"
                )
            es_staff = RolCodigo.ADMIN in roles or RolCodigo.PEDIDOS in roles
            if not es_staff and pedido.usuario_id != usuario_id:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, "No podés ver este pedido"
                )
            pago = uow.pagos.get_ultimo_por_pedido(pedido_id)
            if not pago:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "El pedido no tiene pagos"
                )
            return PagoRead(
                id=pago.id,
                pedido_id=pago.pedido_id,
                mp_payment_id=pago.mp_payment_id,
                mp_preference_id=pago.mp_preference_id,
                mp_status=pago.mp_status,
                mp_status_detail=pago.mp_status_detail,
                transaction_amount=str(pago.transaction_amount),
                currency_id=pago.currency_id,
                created_at=pago.created_at,
                updated_at=pago.updated_at,
            )

    async def _sincronizar_payment(self, mp_payment_id: str) -> Optional[str]:
        # consulta el payment a MP y sincroniza pago + pedido; devuelve mp_status
        sdk = get_sdk()
        resp = await asyncio.to_thread(sdk.payment().get, mp_payment_id)
        data = resp.get("response") or {}
        if resp.get("status") != 200 or not data.get("id"):
            logger.warning("payment %s no encontrado en MP: %s", mp_payment_id, resp)
            return None

        mp_status = data.get("status")
        external_ref = data.get("external_reference")
        if not external_ref or not str(external_ref).isdigit():
            logger.warning("payment %s sin external_reference valido", mp_payment_id)
            return mp_status
        pedido_id = int(external_ref)

        debe_confirmar = False
        with self.uow as uow:
            pedido = uow.pedidos.get_pedido(pedido_id)
            if not pedido:
                logger.warning("payment %s refiere pedido inexistente %s",
                               mp_payment_id, pedido_id)
                return mp_status

            pago = uow.pagos.get_by_mp_payment_id(str(data["id"]))
            if not pago:
                pago = uow.pagos.get_ultimo_por_pedido(pedido_id)
            if not pago:
                # webhook llego sin create-preference previo: registrar igual
                pago = uow.pagos.add(
                    Pago(
                        pedido_id=pedido_id,
                        idempotency_key=str(uuid.uuid4()),
                        transaction_amount=pedido.total,
                        currency_id=CURRENCY,
                    )
                )

            pago.mp_payment_id = str(data["id"])
            pago.mp_status = mp_status or pago.mp_status
            pago.mp_status_detail = data.get("status_detail")
            if data.get("transaction_amount") is not None:
                pago.transaction_amount = data["transaction_amount"]
            pago.updated_at = datetime.now(timezone.utc)
            uow.session.add(pago)

            estado = uow.pedidos.get_estado_by_id(pedido.estado_id)
            debe_confirmar = (
                mp_status == "approved"
                and estado.codigo == EstadoPedidoCodigo.PENDIENTE
            )
            actor_id = pedido.usuario_id

        if debe_confirmar:
            # pago aprobado -> el pedido avanza PENDIENTE -> CONFIRMADO por la FSM
            # (se reusa PedidoService: historial RN-02/03 + evento WS post-commit)
            svc = PedidoService(self.uow)
            try:
                svc.cambiar_estado(
                    pedido_id,
                    EstadoPedidoCodigo.CONFIRMADO,
                    actor_id,
                    {RolCodigo.ADMIN},
                    observacion="Pago aprobado en MercadoPago",
                )
                self.evento_ws = svc.evento_ws
            except HTTPException as e:
                # carrera webhook/confirm: si otro ya confirmo, no es error
                if e.status_code != status.HTTP_409_CONFLICT:
                    raise

        return mp_status
