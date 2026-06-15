from datetime import date
from typing import List

from app.repositories.estadisticas_repository import EstadisticasRepository
from app.schemas.estadisticas_schemas import (
    IngresoFormaPagoItem,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)
from app.uow import UnitOfWork


class EstadisticasService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_resumen(self) -> ResumenResponse:
        with self.uow as uow:
            repo = EstadisticasRepository(uow.session)
            data = repo.get_resumen_kpis()
        return ResumenResponse(**data)

    def get_ventas_periodo(
        self, desde: date, hasta: date, agrupacion: str
    ) -> List[VentasPeriodoItem]:
        with self.uow as uow:
            repo = EstadisticasRepository(uow.session)
            rows = repo.get_ventas_periodo(desde, hasta, agrupacion)
        return [VentasPeriodoItem(**r) for r in rows]

    def get_productos_top(self, limit: int) -> List[ProductoTopItem]:
        with self.uow as uow:
            repo = EstadisticasRepository(uow.session)
            rows = repo.get_productos_top(limit)
        return [ProductoTopItem(**r) for r in rows]

    def get_pedidos_por_estado(self) -> List[PedidosEstadoItem]:
        with self.uow as uow:
            repo = EstadisticasRepository(uow.session)
            rows = repo.get_pedidos_por_estado()
        return [PedidosEstadoItem(**r) for r in rows]

    def get_ingresos_por_forma_pago(
        self, desde: date, hasta: date
    ) -> List[IngresoFormaPagoItem]:
        with self.uow as uow:
            repo = EstadisticasRepository(uow.session)
            rows = repo.get_ingresos_por_forma_pago(desde, hasta)
        return [IngresoFormaPagoItem(**r) for r in rows]
