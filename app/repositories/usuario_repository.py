from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.seguridad import Rol, Usuario, UsuarioRol
from app.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: Session):
        super().__init__(session, Usuario)

    def get_by_email(self, email: str) -> Optional[Usuario]:
        user = self.session.exec(
            select(Usuario).where(
                Usuario.email == email,
                Usuario.deleted_at.is_(None),
            )
        ).first()
        if user:
            _ = [r.codigo for r in user.roles]
        return user

    def get_by_id(
        self, usuario_id: int, *, with_roles: bool = True
    ) -> Optional[Usuario]:
        user = self.session.exec(
            select(Usuario).where(
                Usuario.id == usuario_id,
                Usuario.deleted_at.is_(None),
            )
        ).first()
        if user and with_roles:
            _ = [r.codigo for r in user.roles]
        return user

    def create(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.flush()
        return usuario

    def add_rol(self, usuario_id: int, rol_id: int) -> None:
        existe = self.session.exec(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.rol_id == rol_id,
            )
        ).first()
        if existe:
            return
        self.session.add(UsuarioRol(usuario_id=usuario_id, rol_id=rol_id))

    def remove_rol(self, usuario_id: int, rol_id: int) -> None:
        row = self.session.exec(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.rol_id == rol_id,
            )
        ).first()
        if row:
            self.session.delete(row)

    def clear_roles(self, usuario_id: int) -> None:
        for row in self.session.exec(
            select(UsuarioRol).where(UsuarioRol.usuario_id == usuario_id)
        ):
            self.session.delete(row)

    def soft_delete(self, usuario: Usuario) -> None:
        usuario.deleted_at = datetime.now(timezone.utc)
        self.session.add(usuario)

    def list_paginado(
        self,
        skip: int,
        limit: int,
        rol_codigo: Optional[str] = None,
    ) -> List[Usuario]:
        q = select(Usuario).where(Usuario.deleted_at.is_(None))
        if rol_codigo:
            q = (
                q.join(UsuarioRol)
                .join(Rol)
                .where(Rol.codigo == rol_codigo)
                .distinct()
            )
        q = q.offset(skip).limit(limit)
        usuarios = self.session.exec(q).all()
        for u in usuarios:
            _ = [r.codigo for r in u.roles]
        return usuarios

    def count_filtrado(self, rol_codigo: Optional[str] = None) -> int:
        if rol_codigo:
            rows = self.session.exec(
                select(Usuario.id)
                .join(UsuarioRol)
                .join(Rol)
                .where(Usuario.deleted_at.is_(None), Rol.codigo == rol_codigo)
                .distinct()
            ).all()
            return len(rows)
        return len(
            self.session.exec(
                select(Usuario.id).where(Usuario.deleted_at.is_(None))
            ).all()
        )
