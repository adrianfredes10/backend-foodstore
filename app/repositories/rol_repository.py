from typing import Optional

from sqlmodel import Session, select

from app.models.seguridad import Rol
from app.repositories.base_repository import BaseRepository


class RolRepository(BaseRepository[Rol]):
    def __init__(self, session: Session):
        super().__init__(session, Rol)

    def get_by_codigo(self, codigo: str) -> Optional[Rol]:
        return self.session.exec(select(Rol).where(Rol.codigo == codigo)).first()
