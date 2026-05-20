from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.constants.codigos import RolCodigo
from app.deps.auth_deps import get_current_user, require_roles
from app.models.seguridad import Usuario
from app.schemas.pedido_schemas import (
    CambiarEstadoRequest,
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
def crear_pedido(
    body: PedidoCreate,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).crear(user.id, body)


@router.get("/{pedido_id}", response_model=PedidoRead)
def obtener_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).obtener(pedido_id, user.id, _roles(user))


@router.patch("/{pedido_id}/estado", response_model=PedidoRead)
def cambiar_estado_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    body: CambiarEstadoRequest,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).cambiar_estado(
        pedido_id, body.estado_codigo, user.id, _roles(user), body.observacion
    )


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
def cancelar_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).cancelar(pedido_id, user.id)


@router.post("/{pedido_id}/avanzar", response_model=PedidoRead)
def avanzar_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    staff: Annotated[
        Usuario,
        Depends(require_roles(RolCodigo.ADMIN, RolCodigo.PEDIDOS)),
    ],
    uow: UnitOfWork = Depends(get_uow),
):
    return PedidoService(uow).avanzar_estado(pedido_id, staff.id)
