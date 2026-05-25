from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.pedido import (
    DetallePedido,
    EstadoPedido,
    FormaPago,
    HistorialEstadoPedido,
    Pedido,
)
from app.repositories.base_repository import BaseRepository


class PedidoRepository(BaseRepository[Pedido]):
    def __init__(self, session: Session):
        super().__init__(session, Pedido)

    def get_estado_by_codigo(self, codigo: str) -> Optional[EstadoPedido]:
        return self.session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == codigo)
        ).first()

    def get_estado_by_id(self, estado_id: int) -> Optional[EstadoPedido]:
        return self.session.get(EstadoPedido, estado_id)

    def get_forma_pago(self, forma_id: int) -> Optional[FormaPago]:
        return self.session.get(FormaPago, forma_id)

    def list_formas_pago_activas(self) -> List[FormaPago]:
        return self.session.exec(
            select(FormaPago).where(FormaPago.activa == True).order_by(FormaPago.id)  # noqa: E712
        ).all()

    def list_estados_pedido(self) -> List[EstadoPedido]:
        return self.session.exec(
            select(EstadoPedido).order_by(EstadoPedido.orden)
        ).all()

    def create_pedido(self, pedido: Pedido) -> Pedido:
        self.session.add(pedido)
        self.session.flush()
        return pedido

    def add_detalle(self, detalle: DetallePedido) -> DetallePedido:
        self.session.add(detalle)
        self.session.flush()
        return detalle

    def append_historial(self, row: HistorialEstadoPedido) -> HistorialEstadoPedido:
        self.session.add(row)
        self.session.flush()
        return row

    def get_pedido(self, pedido_id: int) -> Optional[Pedido]:
        pedido = self.session.exec(
            select(Pedido).where(Pedido.id == pedido_id)
        ).first()
        if pedido:
            _ = [d.producto_nombre for d in pedido.detalles]
            _ = [h.fecha for h in pedido.historial]
        return pedido

    def list_for_usuario(
        self,
        usuario_id: int,
        skip: int,
        limit: int,
        estado_codigo: Optional[str] = None,
    ) -> List[Pedido]:
        q = select(Pedido).where(Pedido.usuario_id == usuario_id)
        if estado_codigo:
            q = q.join(EstadoPedido, Pedido.estado_id == EstadoPedido.id).where(
                EstadoPedido.codigo == estado_codigo
            )
        q = q.order_by(Pedido.created_at.desc()).offset(skip).limit(limit)
        return self.session.exec(q).all()

    def list_all(
        self,
        skip: int,
        limit: int,
        estado_codigo: Optional[str] = None,
        usuario_id: Optional[int] = None,
    ) -> List[Pedido]:
        q = select(Pedido)
        if estado_codigo:
            q = q.join(EstadoPedido, Pedido.estado_id == EstadoPedido.id).where(
                EstadoPedido.codigo == estado_codigo
            )
        if usuario_id:
            q = q.where(Pedido.usuario_id == usuario_id)
        q = q.order_by(Pedido.created_at.desc()).offset(skip).limit(limit)
        return self.session.exec(q).all()

    def set_estado(self, pedido: Pedido, nuevo_estado_id: int) -> None:
        pedido.estado_id = nuevo_estado_id
        pedido.updated_at = datetime.now(timezone.utc)
        self.session.add(pedido)
