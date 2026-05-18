from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from app.models.categoria import Categoria, ProductoCategoria
from app.models.producto import Producto
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


class CategoriaRepository:
    """Encapsula el acceso a datos de categorías. No hace commit."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Categoria]:
        statement = (
            select(Categoria)
            .where(Categoria.deleted_at.is_(None))
            .options(selectinload(Categoria.subcategorias))
            .offset(skip)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def count(self) -> int:
        return len(
            self.session.exec(
                select(Categoria).where(Categoria.deleted_at.is_(None))
            ).all()
        )

    def get_by_id(self, categoria_id: int) -> Optional[Categoria]:
        categoria = self.session.get(Categoria, categoria_id)
        if categoria and categoria.deleted_at is not None:
            return None
        return categoria

    def get_by_id_con_subcategorias(self, categoria_id: int) -> Optional[Categoria]:
        categoria = self.session.get(
            Categoria,
            categoria_id,
            options=(selectinload(Categoria.subcategorias),),
        )
        if categoria and categoria.deleted_at is not None:
            return None
        return categoria

    def get_by_nombre(self, nombre: str) -> Optional[Categoria]:
        return self.session.exec(
            select(Categoria).where(
                Categoria.nombre == nombre,
                Categoria.deleted_at.is_(None)
            )
        ).first()

    def get_by_nombre_excluding(self, nombre: str, exclude_id: int) -> Optional[Categoria]:
        return self.session.exec(
            select(Categoria).where(
                Categoria.nombre == nombre,
                Categoria.id != exclude_id,
                Categoria.deleted_at.is_(None)
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

    def delete(self, categoria: Categoria) -> None:
        self.session.delete(categoria)

    def has_productos(self, categoria_id: int) -> bool:
        result = self.session.exec(
            select(ProductoCategoria)
            .join(Producto, ProductoCategoria.producto_id == Producto.id)
            .where(
                ProductoCategoria.categoria_id == categoria_id,
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
