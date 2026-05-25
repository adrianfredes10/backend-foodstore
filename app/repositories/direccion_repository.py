from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.direccion_entrega import DireccionEntrega
from app.repositories.base_repository import BaseRepository


class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session: Session):
        super().__init__(session, DireccionEntrega)

    def list_by_usuario(self, usuario_id: int) -> List[DireccionEntrega]:
        return self.session.exec(
            select(DireccionEntrega)
            .where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.deleted_at.is_(None),
            )
            .order_by(DireccionEntrega.es_principal.desc(), DireccionEntrega.id)
        ).all()

    def get_owned(
        self, direccion_id: int, usuario_id: int
    ) -> Optional[DireccionEntrega]:
        d = super().get_by_id(direccion_id)
        if not d or d.deleted_at is not None or d.usuario_id != usuario_id:
            return None
        return d

    def get_by_id_para_pedido(self, direccion_id: int) -> Optional[DireccionEntrega]:
        # sin filtro de deleted_at: la dirección pudo ser borrada después del pedido
        return self.session.get(DireccionEntrega, direccion_id)

    def create(self, row: DireccionEntrega) -> DireccionEntrega:
        self.session.add(row)
        self.session.flush()
        return row

    def update_fields(self, d: DireccionEntrega, **kwargs) -> DireccionEntrega:
        for k, v in kwargs.items():
            setattr(d, k, v)
        self.session.add(d)
        return d

    def soft_delete(self, d: DireccionEntrega) -> None:
        d.deleted_at = datetime.now(timezone.utc)
        self.session.add(d)

    def clear_principal_usuario(self, usuario_id: int) -> None:
        for d in self.session.exec(
            select(DireccionEntrega).where(
                DireccionEntrega.usuario_id == usuario_id,
                DireccionEntrega.deleted_at.is_(None),
            )
        ):
            d.es_principal = False
            self.session.add(d)
