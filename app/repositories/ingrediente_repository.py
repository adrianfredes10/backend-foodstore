from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.ingrediente import Ingrediente, ProductoIngrediente
from app.models.producto import Producto
from app.repositories.base_repository import BaseRepository
from app.schemas.ingrediente import IngredienteCreate, IngredienteUpdate


class IngredienteRepository(BaseRepository[Ingrediente]):
    def __init__(self, session: Session):
        super().__init__(session, Ingrediente)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Ingrediente]:
        statement = (
            select(Ingrediente)
            .where(Ingrediente.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def count(self) -> int:
        return len(
            self.session.exec(
                select(Ingrediente).where(Ingrediente.deleted_at.is_(None))
            ).all()
        )

    def get_by_id(self, ingrediente_id: int) -> Optional[Ingrediente]:
        ing = super().get_by_id(ingrediente_id)
        if ing is None or ing.deleted_at is not None:
            return None
        return ing

    def get_by_nombre(self, nombre: str) -> Optional[Ingrediente]:
        return self.session.exec(
            select(Ingrediente).where(
                Ingrediente.nombre == nombre,
                Ingrediente.deleted_at.is_(None),
            )
        ).first()

    def get_by_nombre_excluding(
        self, nombre: str, exclude_id: int
    ) -> Optional[Ingrediente]:
        return self.session.exec(
            select(Ingrediente).where(
                Ingrediente.nombre == nombre,
                Ingrediente.id != exclude_id,
                Ingrediente.deleted_at.is_(None),
            )
        ).first()

    def create(self, ingrediente_data: IngredienteCreate) -> Ingrediente:
        ingrediente = Ingrediente.model_validate(ingrediente_data)
        self.session.add(ingrediente)
        return ingrediente

    def update(
        self, ingrediente: Ingrediente, ingrediente_data: IngredienteUpdate
    ) -> Ingrediente:
        ingrediente.nombre = ingrediente_data.nombre
        ingrediente.unidad_medida = ingrediente_data.unidad_medida
        ingrediente.stock_actual = ingrediente_data.stock_actual
        ingrediente.stock_minimo = ingrediente_data.stock_minimo
        self.session.add(ingrediente)
        return ingrediente

    def soft_delete(self, ingrediente: Ingrediente) -> None:
        ingrediente.deleted_at = datetime.now(timezone.utc)
        self.session.add(ingrediente)

    def delete(self, ingrediente: Ingrediente) -> None:
        self.session.delete(ingrediente)

    def has_productos(self, ingrediente_id: int) -> bool:
        result = self.session.exec(
            select(ProductoIngrediente)
            .join(Producto, ProductoIngrediente.producto_id == Producto.id)
            .where(
                ProductoIngrediente.ingrediente_id == ingrediente_id,
                Producto.deleted_at.is_(None),
            )
        ).first()
        return result is not None
