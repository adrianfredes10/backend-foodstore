from typing import Annotated, Optional, List
from fastapi import APIRouter, Query, Path, Depends, status
from app.uow import UnitOfWork, get_uow
from app.services.producto_service import ProductoService
from app.schemas.producto import ProductoCreate, ProductoRead, ProductoUpdate

router = APIRouter(prefix="/api/productos", tags=["productos"])


@router.get("", response_model=List[ProductoRead])
def get_productos(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    categoria_id: Annotated[Optional[int], Query(gt=0)] = None,
    uow: UnitOfWork = Depends(get_uow)
):
    """Lista todos los productos con sus relaciones"""
    service = ProductoService(uow)
    return service.get_all(skip, limit, categoria_id)


@router.get("/{id}", response_model=ProductoRead)
def get_producto(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene un producto por ID con todas sus relaciones"""
    service = ProductoService(uow)
    return service.get_by_id(id)


@router.post("", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto_data: ProductoCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Crea un nuevo producto con sus categorías e ingredientes"""
    service = ProductoService(uow)
    return service.create(producto_data)


@router.put("/{id}", response_model=ProductoRead)
def update_producto(
    id: Annotated[int, Path(gt=0)],
    producto_data: ProductoUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Actualiza un producto existente"""
    service = ProductoService(uow)
    return service.update(id, producto_data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow)
):
    """Elimina un producto"""
    service = ProductoService(uow)
    service.delete(id)
    return None
