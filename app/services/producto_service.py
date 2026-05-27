from typing import Optional

from fastapi import HTTPException, status

from app.models.producto import Producto
from app.schemas.common import PaginatedResponse
from app.schemas.producto import ProductoCreate, ProductoRead, ProductoUpdate
from app.uow import UnitOfWork


class ProductoService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all(
        self,
        page: int = 1,
        size: int = 20,
        categoria_id: Optional[int] = None,
        disponible: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> PaginatedResponse:
        skip = (page - 1) * size
        with self.uow as uow:
            items = uow.productos.get_all(
                skip=skip,
                limit=size,
                categoria_id=categoria_id,
                disponible=disponible,
                q=q,
            )
            total = uow.productos.count(
                categoria_id=categoria_id, disponible=disponible, q=q
            )
            pages = max(1, -(-total // size))
            return PaginatedResponse(
                items=[uow.productos.build_producto_read(p) for p in items],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    def get_by_id(self, producto_id: int) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            return uow.productos.build_producto_read(producto)

    def create(self, producto_data: ProductoCreate) -> ProductoRead:
        with self.uow as uow:
            if uow.productos.get_by_nombre(producto_data.nombre):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Producto ya existe",
                )
            cat = uow.productos.get_categoria_by_id(producto_data.categoria_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {producto_data.categoria_id} no encontrada",
                )
            producto = Producto(
                nombre=producto_data.nombre,
                descripcion=producto_data.descripcion,
                precio=producto_data.precio,
                disponible=producto_data.disponible,
                stock_cantidad=producto_data.stock_cantidad,
                imagen_url=producto_data.imagen_url,
                categoria_id=producto_data.categoria_id,
            )
            uow.productos.create(producto)
            uow.flush()

            for ing_input in producto_data.ingredientes:
                ing = uow.productos.get_ingrediente_by_id(ing_input.ingrediente_id)
                if not ing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Ingrediente con ID {ing_input.ingrediente_id} no encontrado",
                    )
                uow.productos.add_ingrediente(
                    producto.id,
                    ing_input.ingrediente_id,
                    ing_input.cantidad,
                    ing_input.es_alergeno,
                )

            uow.flush()
            uow.refresh(producto)
            return uow.productos.build_producto_read(producto)

    def update(self, producto_id: int, producto_data: ProductoUpdate) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            if uow.productos.get_by_nombre_excluding(producto_data.nombre, producto_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro producto con ese nombre",
                )
            cat = uow.productos.get_categoria_by_id(producto_data.categoria_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {producto_data.categoria_id} no encontrada",
                )
            uow.productos.update(producto, producto_data)
            uow.productos.clear_ingredientes(producto_id)
            uow.flush()

            for ing_input in producto_data.ingredientes:
                ing = uow.productos.get_ingrediente_by_id(ing_input.ingrediente_id)
                if not ing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Ingrediente con ID {ing_input.ingrediente_id} no encontrado",
                    )
                uow.productos.add_ingrediente(
                    producto_id,
                    ing_input.ingrediente_id,
                    ing_input.cantidad,
                    ing_input.es_alergeno,
                )

            uow.flush()
            uow.refresh(producto)
            return uow.productos.build_producto_read(producto)

    def delete(self, producto_id: int) -> None:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            uow.productos.clear_ingredientes(producto_id)
            uow.productos.soft_delete(producto)

    def set_disponibilidad(self, producto_id: int, disponible: bool) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            uow.productos.set_disponible(producto, disponible)
            uow.flush()
            return uow.productos.build_producto_read(producto)

    def set_stock_cantidad(self, producto_id: int, stock: float) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )
            uow.productos.set_stock_cantidad(producto, stock)
            uow.flush()
            return uow.productos.build_producto_read(producto)
