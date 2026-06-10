from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.constants.codigos import RolCodigo
from app.core.auth_deps import get_current_user, require_roles
from app.core.ws_manager import manager
from app.models.seguridad import Usuario
from app.schemas.pedido_schemas import (
    CambiarEstadoRequest,
    CancelarRequest,
    HistorialEstadoRead,
    PedidoCreate,
    PedidoRead,
)
from app.services.pedido_service import PedidoService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["pedidos"])


def _roles(user: Usuario) -> set[str]:
    return {r.codigo for r in (user.roles or [])}


def _es_staff(roles: set[str]) -> bool:
    return RolCodigo.ADMIN in roles or RolCodigo.PEDIDOS in roles


async def _emitir_evento(svc: PedidoService) -> None:
    # broadcast post-commit, fuera del UoW (RN-06)
    ev = svc.evento_ws
    if not ev:
        return
    await manager.broadcast_to_roles([RolCodigo.ADMIN, RolCodigo.PEDIDOS], ev)
    await manager.broadcast_to_order(ev["pedido_id"], ev)


@router.get("", response_model=List[PedidoRead])
def listar_pedidos(
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 20,
    estado_codigo: Annotated[Optional[str], Query()] = None,
    usuario_id: Annotated[Optional[int], Query(gt=0)] = None,
):
    roles = _roles(user)
    es_staff = _es_staff(roles)
    # solo staff puede filtrar por usuario_id ajeno
    filtro_uid = usuario_id if es_staff else None
    svc = PedidoService(uow)
    return svc.listar(
        usuario_id=user.id,
        es_staff=es_staff,
        page=page,
        size=size,
        estado_codigo=estado_codigo,
        filtro_usuario_id=filtro_uid,
    )


@router.post("", response_model=PedidoRead, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    body: PedidoCreate,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    svc = PedidoService(uow)
    read = svc.crear(user.id, body)
    await _emitir_evento(svc)
    return read


@router.get("/{pedido_id}", response_model=PedidoRead)
def obtener_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).obtener(pedido_id, user.id, _roles(user))


@router.patch("/{pedido_id}/estado", response_model=PedidoRead)
async def cambiar_estado_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    body: CambiarEstadoRequest,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    svc = PedidoService(uow)
    read = svc.cambiar_estado(
        pedido_id, body.estado_codigo, user.id, _roles(user), body.observacion
    )
    await _emitir_evento(svc)
    return read


@router.get("/{pedido_id}/historial", response_model=List[HistorialEstadoRead])
def obtener_historial(
    pedido_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).obtener_historial(
        pedido_id, user.id, _roles(user)
    )


@router.post("/{pedido_id}/cancelar", response_model=PedidoRead)
async def cancelar_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    body: CancelarRequest,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    svc = PedidoService(uow)
    read = svc.cancelar(pedido_id, user.id, body.motivo)
    await _emitir_evento(svc)
    return read


@router.post("/{pedido_id}/avanzar", response_model=PedidoRead)
async def avanzar_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    staff: Annotated[
        Usuario,
        Depends(require_roles(RolCodigo.ADMIN, RolCodigo.PEDIDOS)),
    ],
    uow: UnitOfWork = Depends(get_uow),
):
    svc = PedidoService(uow)
    read = svc.avanzar_estado(pedido_id, staff.id)
    await _emitir_evento(svc)
    return read
