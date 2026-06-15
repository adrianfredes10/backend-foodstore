# pagos MercadoPago (CONTRATO-API §PAGOS)
# flujo: create-preference -> redirect a init_point -> webhook IPN -> redirect -> confirm
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.responses import RedirectResponse

from app.constants.codigos import RolCodigo
from app.core.auth_deps import get_current_user
from app.core.config import get_settings
from app.core.ws_manager import manager
from app.models.seguridad import Usuario
from app.schemas.pago_schemas import (
    PagoConfirmRequest,
    PagoCreateRequest,
    PagoCrearResponse,
    PagoEstadoResponse,
    PagoRead,
)
from app.services.pago_service import PagoService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["pagos"])

REDIRECT_STATUS_VALIDOS = {"success", "failure", "pending"}


async def _emitir_evento(svc: PagoService) -> None:
    # broadcast post-commit, fuera del UoW (RN-06): el webhook pudo confirmar el pedido
    ev = svc.evento_ws
    if not ev:
        return
    await manager.broadcast_to_roles([RolCodigo.ADMIN, RolCodigo.PEDIDOS], ev)
    await manager.broadcast_to_order(ev["data"]["pedido_id"], ev)


@router.post(
    "/create-preference",
    response_model=PagoCrearResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_preference(
    body: PagoCreateRequest,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return await PagoService(uow).create_preference(body.pedido_id, user.id)


@router.post("/webhook")
async def webhook(
    request: Request,
    uow: UnitOfWork = Depends(get_uow),
):
    # endpoint publico: MP no manda cookie; responde 200 siempre
    # MP notifica por query params (?topic=payment&id=) o por body JSON
    payment_id = None
    params = request.query_params
    if params.get("type") == "payment" or params.get("topic") == "payment":
        payment_id = params.get("data.id") or params.get("id")
    if not payment_id:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict) and body.get("type") == "payment":
            payment_id = (body.get("data") or {}).get("id")

    svc = PagoService(uow)
    await svc.procesar_webhook(payment_id)
    await _emitir_evento(svc)
    return {"status": "ok"}


@router.post("/confirm", response_model=PagoEstadoResponse)
async def confirm(
    body: PagoConfirmRequest,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    svc = PagoService(uow)
    resp = await svc.confirm(body.pedido_id, user.id, body.payment_id)
    await _emitir_evento(svc)
    return resp


@router.get("/redirect/{pedido_id}/{redirect_status}")
async def redirect_post_pago(
    pedido_id: Annotated[int, Path(gt=0)],
    redirect_status: str,
):
    # MP redirige aca al usuario despues del checkout (sin cookie de sesion);
    # se lo reenvia a la pagina de resultado de la tienda
    if redirect_status not in REDIRECT_STATUS_VALIDOS:
        redirect_status = "failure"
    front = get_settings().FRONTEND_URL.rstrip("/")
    return RedirectResponse(
        url=f"{front}/pedidos/{pedido_id}/pago/{redirect_status}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/pedido/{pedido_id}", response_model=PagoRead)
def obtener_pago_de_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    # read-only para el detalle de pedido (cliente dueno o staff)
    roles = {r.codigo for r in (user.roles or [])}
    return PagoService(uow).obtener_por_pedido(pedido_id, user.id, roles)
