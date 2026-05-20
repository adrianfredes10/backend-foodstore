from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.constants.codigos import RolCodigo
from app.deps.auth_deps import require_roles
from app.models.seguridad import Usuario
from app.schemas.common import PaginatedResponse
from app.schemas.producto import (
    ProductoCreate,
    ProductoDisponibilidadBody,
    ProductoRead,
    ProductoStockBody,
    ProductoUpdate,
)
from app.services.producto_service import ProductoService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["productos"])


@router.get("", response_model=PaginatedResponse)
def get_productos(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    categoria_id: Annotated[Optional[int], Query(gt=0)] = None,
    disponible: Annotated[Optional[bool], Query()] = None,
    q: Annotated[Optional[str], Query(max_length=200)] = None,
    uow: UnitOfWork = Depends(get_uow),
):
    return ProductoService(uow).get_all(
        page=page,
        size=size,
        categoria_id=categoria_id,
        disponible=disponible,
        q=q,
    )


@router.get("/{id}", response_model=ProductoRead)
def get_producto(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow),
):
    return ProductoService(uow).get_by_id(id)


@router.post("", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto_data: ProductoCreate,
    *,
    uow: UnitOfWork = Depends(get_uow),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
):
    return ProductoService(uow).create(producto_data)


@router.put("/{id}", response_model=ProductoRead)
def update_producto(
    id: Annotated[int, Path(gt=0)],
    producto_data: ProductoUpdate,
    *,
    uow: UnitOfWork = Depends(get_uow),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
):
    return ProductoService(uow).update(id, producto_data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(
    id: Annotated[int, Path(gt=0)],
    *,
    uow: UnitOfWork = Depends(get_uow),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
):
    ProductoService(uow).delete(id)


@router.patch("/{id}/stock", response_model=ProductoRead)
def patch_stock(
    id: Annotated[int, Path(gt=0)],
    body: ProductoStockBody,
    *,
    uow: UnitOfWork = Depends(get_uow),
    _user: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN, RolCodigo.STOCK))],
):
    return ProductoService(uow).set_stock_cantidad(id, body.stock_cantidad)


@router.patch("/{id}/disponibilidad", response_model=ProductoRead)
def patch_disponibilidad(
    id: Annotated[int, Path(gt=0)],
    body: ProductoDisponibilidadBody,
    *,
    uow: UnitOfWork = Depends(get_uow),
    _user: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN, RolCodigo.STOCK))],
):
    return ProductoService(uow).set_disponibilidad(id, body.disponible)
