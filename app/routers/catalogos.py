from typing import List

from fastapi import APIRouter, Depends

from app.schemas.catalogo_schemas import EstadoPedidoRead, FormaPagoRead
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["catalogos"])


@router.get("/formas-pago", response_model=List[FormaPagoRead])
def listar_formas_pago(uow: UnitOfWork = Depends(get_uow)):
    with uow:
        return [
            FormaPagoRead(id=fp.id, codigo=fp.codigo, nombre=fp.nombre, activa=fp.activa)
            for fp in uow.pedidos.list_formas_pago_activas()
        ]


@router.get("/estados-pedido", response_model=List[EstadoPedidoRead])
def listar_estados_pedido(uow: UnitOfWork = Depends(get_uow)):
    with uow:
        return [
            EstadoPedidoRead(id=e.id, codigo=e.codigo, nombre=e.nombre, orden=e.orden)
            for e in uow.pedidos.list_estados_pedido()
        ]
