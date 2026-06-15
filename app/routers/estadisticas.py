from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from app.constants.codigos import RolCodigo
from app.core.auth_deps import require_roles
from app.models.seguridad import Usuario
from app.schemas.estadisticas_schemas import (
    IngresoFormaPagoItem,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)
from app.services.estadisticas_service import EstadisticasService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["estadisticas"])


@router.get("/resumen", response_model=ResumenResponse)
def resumen(
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    return EstadisticasService(uow).get_resumen()


@router.get("/ventas", response_model=List[VentasPeriodoItem])
def ventas_periodo(
    desde: date = Query(...),
    hasta: date = Query(...),
    agrupacion: str = Query(default="day", pattern="^(day|week|month)$"),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))] = None,
    uow: UnitOfWork = Depends(get_uow),
):
    return EstadisticasService(uow).get_ventas_periodo(desde, hasta, agrupacion)


@router.get("/productos-top", response_model=List[ProductoTopItem])
def productos_top(
    limit: int = Query(default=10, ge=1, le=50),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))] = None,
    uow: UnitOfWork = Depends(get_uow),
):
    return EstadisticasService(uow).get_productos_top(limit)


@router.get("/pedidos-por-estado", response_model=List[PedidosEstadoItem])
def pedidos_por_estado(
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    return EstadisticasService(uow).get_pedidos_por_estado()


@router.get("/ingresos", response_model=List[IngresoFormaPagoItem])
def ingresos_por_forma_pago(
    desde: date = Query(...),
    hasta: date = Query(...),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))] = None,
    uow: UnitOfWork = Depends(get_uow),
):
    return EstadisticasService(uow).get_ingresos_por_forma_pago(desde, hasta)
