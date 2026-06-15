from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from app.models.categoria import Categoria
from app.models.ingrediente import Ingrediente, ProductoIngrediente
from app.models.producto import Producto
from app.repositories.base_repository import BaseRepository
from app.schemas.categoria import CategoriaRead
from app.schemas.producto import (
    ProductoIngredienteInput,
    ProductoIngredienteRead,
    ProductoRead,
    ProductoUpdate,
)


class ProductoRepository(BaseRepository[Producto]):
    def __init__(self, session: Session):
        super().__init__(session, Producto)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        categoria_id: Optional[int] = None,
        disponible: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> List[Producto]:
        query = select(Producto).where(Producto.deleted_at.is_(None))
        if categoria_id:
            query = query.where(Producto.categoria_id == categoria_id)
        if disponible is not None:
            query = query.where(Producto.disponible == disponible)
        if q:
            query = query.where(Producto.nombre.ilike(f"%{q.strip()}%"))
        return self.session.exec(query.offset(skip).limit(limit)).all()

    def count(
        self,
        categoria_id: Optional[int] = None,
        disponible: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> int:
        query = select(Producto).where(Producto.deleted_at.is_(None))
        if categoria_id:
            query = query.where(Producto.categoria_id == categoria_id)
        if disponible is not None:
            query = query.where(Producto.disponible == disponible)
        if q:
            query = query.where(Producto.nombre.ilike(f"%{q.strip()}%"))
        return len(self.session.exec(query).all())

    def get_by_id(self, producto_id: int) -> Optional[Producto]:
        p = super().get_by_id(producto_id)
        if p is None or p.deleted_at is not None:
            return None
        return p

    def get_by_nombre(self, nombre: str) -> Optional[Producto]:
        return self.session.exec(
            select(Producto).where(
                Producto.nombre == nombre,
                Producto.deleted_at.is_(None),
            )
        ).first()

    def get_by_nombre_excluding(self, nombre: str, exclude_id: int) -> Optional[Producto]:
        return self.session.exec(
            select(Producto).where(
                Producto.nombre == nombre,
                Producto.id != exclude_id,
                Producto.deleted_at.is_(None),
            )
        ).first()

    def create(self, producto: Producto) -> Producto:
        self.session.add(producto)
        return producto

    def update(self, producto: Producto, producto_data: ProductoUpdate) -> Producto:
        producto.nombre = producto_data.nombre
        producto.descripcion = producto_data.descripcion
        producto.precio = producto_data.precio
        producto.disponible = producto_data.disponible
        producto.stock_cantidad = producto_data.stock_cantidad
        producto.imagen_url = producto_data.imagen_url
        producto.categoria_id = producto_data.categoria_id
        self.session.add(producto)
        return producto

    def set_disponible(self, producto: Producto, disponible: bool) -> Producto:
        producto.disponible = disponible
        self.session.add(producto)
        return producto

    def set_stock_cantidad(self, producto: Producto, stock: float) -> Producto:
        producto.stock_cantidad = stock
        self.session.add(producto)
        return producto

    def soft_delete(self, producto: Producto) -> None:
        producto.deleted_at = datetime.now(timezone.utc)
        self.session.add(producto)

    def get_ingredientes_con_pivot(
        self, producto_id: int
    ) -> list[tuple["Ingrediente", "ProductoIngrediente"]]:
        rows = self.session.exec(
            select(Ingrediente, ProductoIngrediente)
            .join(
                ProductoIngrediente,
                ProductoIngrediente.ingrediente_id == Ingrediente.id,
            )
            .where(
                ProductoIngrediente.producto_id == producto_id,
                Ingrediente.deleted_at.is_(None),
            )
        ).all()
        return list(rows)

    def add_ingrediente(
        self,
        producto_id: int,
        ingrediente_id: int,
        cantidad: float,
        es_alergeno: bool = False,
        es_removible: bool = False,
        unidad_medida_id: Optional[int] = None,
    ) -> ProductoIngrediente:
        link = ProductoIngrediente(
            producto_id=producto_id,
            ingrediente_id=ingrediente_id,
            cantidad=cantidad,
            es_alergeno=es_alergeno,
            es_removible=es_removible,
            unidad_medida_id=unidad_medida_id,
        )
        self.session.add(link)
        self.session.flush()
        return link

    def assign_ingredientes(
        self, producto_id: int, ingredientes_data: List[ProductoIngredienteInput]
    ) -> None:
        for ing_data in ingredientes_data:
            self.session.add(
                ProductoIngrediente(
                    producto_id=producto_id,
                    ingrediente_id=ing_data.ingrediente_id,
                    cantidad=ing_data.cantidad,
                    es_alergeno=ing_data.es_alergeno,
                    es_removible=ing_data.es_removible,
                    unidad_medida_id=ing_data.unidad_medida_id,
                )
            )

    def clear_ingredientes(self, producto_id: int) -> None:
        for rel in self.session.exec(
            select(ProductoIngrediente).where(
                ProductoIngrediente.producto_id == producto_id
            )
        ):
            self.session.delete(rel)

    def get_categoria_by_id(self, categoria_id: int) -> Optional[Categoria]:
        categoria = self.session.get(Categoria, categoria_id)
        if categoria and categoria.deleted_at is not None:
            return None
        return categoria

    def get_ingrediente_by_id(self, ingrediente_id: int) -> Optional[Ingrediente]:
        ingrediente = self.session.get(Ingrediente, ingrediente_id)
        if ingrediente and ingrediente.deleted_at is not None:
            return None
        return ingrediente

    def build_producto_read(self, producto: Producto) -> ProductoRead:
        # categoria (1:N)
        categoria_obj = None
        if producto.categoria_id:
            cat = self.session.get(Categoria, producto.categoria_id)
            if cat and cat.deleted_at is None:
                categoria_obj = CategoriaRead(
                    id=cat.id,
                    nombre=cat.nombre,
                    descripcion=cat.descripcion,
                    parent_id=cat.parent_id,
                    activa=cat.activa,
                    created_at=cat.created_at,
                    subcategorias=[],
                )

        ingredientes_raw = self.session.exec(
            select(Ingrediente, ProductoIngrediente)
            .join(
                ProductoIngrediente,
                ProductoIngrediente.ingrediente_id == Ingrediente.id,
            )
            .where(
                ProductoIngrediente.producto_id == producto.id,
                Ingrediente.deleted_at.is_(None),
            )
        ).all()

        ingredientes = [
            ProductoIngredienteRead(
                ingrediente_id=ing.id,
                nombre=ing.nombre,
                cantidad=pivot.cantidad,
                unidad_medida=ing.unidad_medida,
                es_alergeno=pivot.es_alergeno,
                es_removible=pivot.es_removible,
                unidad_medida_id=pivot.unidad_medida_id,
            )
            for ing, pivot in ingredientes_raw
        ]

        imagenes_url = [
            img["url"]
            for img in (producto.imagenes_data or [])
            if isinstance(img, dict) and img.get("url")
        ]

        return ProductoRead(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=str(producto.precio),
            disponible=producto.disponible,
            stock_cantidad=producto.stock_cantidad,
            imagen_url=producto.imagen_url,
            created_at=producto.created_at,
            categoria=categoria_obj,
            ingredientes=ingredientes,
            imagenes_url=imagenes_url,
        )
