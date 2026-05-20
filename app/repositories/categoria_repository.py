from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.categoria import Categoria
from app.models.producto import Producto
from app.repositories.base_repository import BaseRepository
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session: Session):
        super().__init__(session, Categoria)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        activa: Optional[bool] = None,
    ) -> List[Categoria]:
        statement = (
            select(Categoria)
            .where(Categoria.deleted_at.is_(None))
            .options(selectinload(Categoria.subcategorias))
        )
        if parent_id is not None:
            statement = statement.where(Categoria.parent_id == parent_id)
        if activa is not None:
            statement = statement.where(Categoria.activa == activa)
        statement = statement.offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def count(self, activa: Optional[bool] = None) -> int:
        q = select(Categoria).where(Categoria.deleted_at.is_(None))
        if activa is not None:
            q = q.where(Categoria.activa == activa)
        return len(self.session.exec(q).all())

    # ids bajo root_id (incluye root) con cte recursivo en postgres
    def list_subarbol_recursivo(
        self, root_id: int, skip: int, limit: int
    ) -> List[Categoria]:
        sql = text(
            """
            WITH RECURSIVE arbol AS (
                SELECT id FROM categoria
                WHERE id = :root_id AND deleted_at IS NULL
                UNION ALL
                SELECT c.id FROM categoria c
                INNER JOIN arbol a ON c.parent_id = a.id
                WHERE c.deleted_at IS NULL
            )
            SELECT id FROM arbol ORDER BY id
            """
        )
        rows = self.session.connection().execute(sql, {"root_id": root_id})
        all_ids = [r[0] for r in rows.fetchall()]
        if not all_ids:
            return []
        sliced = all_ids[skip : skip + limit]
        if not sliced:
            return []
        stmt = (
            select(Categoria)
            .where(Categoria.id.in_(sliced))
            .where(Categoria.deleted_at.is_(None))
            .options(selectinload(Categoria.subcategorias))
        )
        out = list(self.session.exec(stmt).all())
        order = {cid: n for n, cid in enumerate(sliced)}
        out.sort(key=lambda c: order.get(c.id, 9999))
        return out

    def get_by_id(self, categoria_id: int) -> Optional[Categoria]:
        categoria = super().get_by_id(categoria_id)
        if categoria is None or categoria.deleted_at is not None:
            return None
        return categoria

    def get_by_id_con_subcategorias(self, categoria_id: int) -> Optional[Categoria]:
        categoria = self.session.get(
            Categoria,
            categoria_id,
            options=(selectinload(Categoria.subcategorias),),
        )
        if categoria is None or categoria.deleted_at is not None:
            return None
        return categoria

    def get_by_nombre(self, nombre: str) -> Optional[Categoria]:
        return self.session.exec(
            select(Categoria).where(
                Categoria.nombre == nombre,
                Categoria.deleted_at.is_(None),
            )
        ).first()

    def get_by_nombre_excluding(
        self, nombre: str, exclude_id: int
    ) -> Optional[Categoria]:
        return self.session.exec(
            select(Categoria).where(
                Categoria.nombre == nombre,
                Categoria.id != exclude_id,
                Categoria.deleted_at.is_(None),
            )
        ).first()

    def create(self, categoria_data: CategoriaCreate) -> Categoria:
        categoria = Categoria.model_validate(categoria_data)
        self.session.add(categoria)
        return categoria

    def update(self, categoria: Categoria, categoria_data: CategoriaUpdate) -> Categoria:
        categoria.nombre = categoria_data.nombre
        categoria.descripcion = categoria_data.descripcion
        dumped = categoria_data.model_dump(exclude_unset=True)
        if "parent_id" in dumped:
            categoria.parent_id = dumped["parent_id"]
        self.session.add(categoria)
        return categoria

    def soft_delete(self, categoria: Categoria) -> None:
        categoria.deleted_at = datetime.now(timezone.utc)
        self.session.add(categoria)

    def has_productos(self, categoria_id: int) -> bool:
        # 1:N: basta con buscar un producto activo con esa categoria_id
        result = self.session.exec(
            select(Producto).where(
                Producto.categoria_id == categoria_id,
                Producto.deleted_at.is_(None),
            )
        ).first()
        return result is not None

    def validate_no_cycle(self, categoria_id: int, new_parent_id: int) -> bool:
        current_id = new_parent_id
        visited: set[int] = set()
        while current_id is not None:
            if current_id == categoria_id:
                return False
            if current_id in visited:
                return False
            visited.add(current_id)
            parent = self.session.get(Categoria, current_id)
            if parent is None:
                break
            current_id = parent.parent_id
        return True

    def get_subcategorias(self, categoria_id: int) -> List[Categoria]:
        return self.session.exec(
            select(Categoria).where(
                Categoria.parent_id == categoria_id,
                Categoria.deleted_at.is_(None),
            )
        ).all()
