from typing import Optional

from sqlmodel import Session, select

from app.models.pago import Pago
from app.repositories.base_repository import BaseRepository


class PagoRepository(BaseRepository[Pago]):
    def __init__(self, session: Session):
        super().__init__(session, Pago)

    def add(self, pago: Pago) -> Pago:
        self.session.add(pago)
        self.session.flush()
        return pago

    def get_ultimo_por_pedido(self, pedido_id: int) -> Optional[Pago]:
        return self.session.exec(
            select(Pago)
            .where(Pago.pedido_id == pedido_id)
            .order_by(Pago.id.desc())
        ).first()

    def get_by_mp_payment_id(self, mp_payment_id: str) -> Optional[Pago]:
        return self.session.exec(
            select(Pago).where(Pago.mp_payment_id == mp_payment_id)
        ).first()
