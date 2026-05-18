from typing import Optional, List
from fastapi import HTTPException, status
from app.uow import UnitOfWork
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoRead
from app.models.producto import Producto


class ProductoService:
    """Orquesta la lógica de negocio de productos usando UnitOfWork. Sin SQL directo, sin commit."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all(self, skip: int = 0, limit: int = 100, categoria_id: Optional[int] = None) -> List[ProductoRead]:
        with self.uow as uow:
            productos = uow.productos.get_all(skip=skip, limit=limit, categoria_id=categoria_id)
            # build_producto_read ya devuelve un schema (ProductoRead), no un modelo
            items = [uow.productos.build_producto_read(p) for p in productos]
            return items

    def get_by_id(self, producto_id: int) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado"
                )
            return uow.productos.build_producto_read(producto)

    def create(self, producto_data: ProductoCreate) -> ProductoRead:
        with self.uow as uow:
            # Validar duplicado
            if uow.productos.get_by_nombre(producto_data.nombre):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Producto ya existe"
                )

            # Crear objeto Producto directamente (sin pasar schema)
            producto = Producto(
                nombre=producto_data.nombre,
                descripcion=producto_data.descripcion,
                precio=producto_data.precio,
                disponible=producto_data.disponible,
            )
            uow.productos.create(producto)
            uow.flush()  # obtener ID asignado por la BD

            # Asociar categorías — una por una, validando existencia
            for cat_id in producto_data.categoria_ids:
                cat = uow.productos.get_categoria_by_id(cat_id)
                if not cat:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Categoría con ID {cat_id} no encontrada",
                    )
                uow.productos.add_categoria(producto.id, cat_id)

            # Asociar ingredientes — uno por uno, validando existencia
            for ing_input in producto_data.ingredientes:
                ing = uow.productos.get_ingrediente_by_id(ing_input.ingrediente_id)
                if not ing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Ingrediente con ID {ing_input.ingrediente_id} no encontrado",
                    )
                uow.productos.add_ingrediente(producto.id, ing_input.ingrediente_id, ing_input.cantidad)

            uow.flush()
            uow.refresh(producto)
            # Forzar carga de relaciones dentro del contexto de la sesión
            _ = producto.categorias
            _ = producto.ingredientes
            return uow.productos.build_producto_read(producto)

    def update(self, producto_id: int, producto_data: ProductoUpdate) -> ProductoRead:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado"
                )

            if uow.productos.get_by_nombre_excluding(producto_data.nombre, producto_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro producto con ese nombre"
                )

            # Actualizar campos del producto
            uow.productos.update(producto, producto_data)

            # Limpiar relaciones anteriores
            uow.productos.clear_categorias(producto_id)
            uow.productos.clear_ingredientes(producto_id)
            uow.flush()

            # Reasociar categorías — una por una, validando existencia
            for cat_id in producto_data.categoria_ids:
                cat = uow.productos.get_categoria_by_id(cat_id)
                if not cat:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Categoría con ID {cat_id} no encontrada",
                    )
                uow.productos.add_categoria(producto_id, cat_id)

            # Reasociar ingredientes — uno por uno, validando existencia
            for ing_input in producto_data.ingredientes:
                ing = uow.productos.get_ingrediente_by_id(ing_input.ingrediente_id)
                if not ing:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Ingrediente con ID {ing_input.ingrediente_id} no encontrado",
                    )
                uow.productos.add_ingrediente(producto_id, ing_input.ingrediente_id, ing_input.cantidad)

            uow.flush()
            uow.refresh(producto)
            _ = producto.categorias
            _ = producto.ingredientes
            return uow.productos.build_producto_read(producto)

    def delete(self, producto_id: int) -> None:
        with self.uow as uow:
            producto = uow.productos.get_by_id(producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado"
                )
            uow.productos.clear_categorias(producto_id)
            uow.productos.clear_ingredientes(producto_id)
            uow.productos.soft_delete(producto)
