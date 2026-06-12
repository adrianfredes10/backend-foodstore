from typing import List

from fastapi import APIRouter, Depends

from app.schemas.catalogo_schemas import (
    EstadoPedidoRead,
    FormaPagoRead,
    UnidadMedidaRead,
)
from app.services.pedido_service import TRANSICIONES
from app.uow import UnitOfWork, get_uow

# estados vigentes de la FSM v7; en bases migradas puede quedar EN_CAMINO
# en la tabla (el historial viejo lo referencia, RN-03) pero no se expone
ESTADOS_FSM = set(TRANSICIONES.keys())

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
            EstadoPedidoRead(
                id=e.id,
                codigo=e.codigo,
                nombre=e.nombre,
                orden=e.orden,
                es_terminal=e.es_terminal,
            )
            for e in uow.pedidos.list_estados_pedido()
            if e.codigo in ESTADOS_FSM
        ]


@router.get("/unidades-medida", response_model=List[UnidadMedidaRead])
def listar_unidades_medida(uow: UnitOfWork = Depends(get_uow)):
    with uow:
        return [
            UnidadMedidaRead(
                id=u.id, nombre=u.nombre, simbolo=u.simbolo, tipo=u.tipo
            )
            for u in uow.ingredientes.list_unidades_medida()
        ]
