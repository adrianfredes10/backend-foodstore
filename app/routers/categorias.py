from typing import Annotated, List
from fastapi import APIRouter, Query, Path, status, Depends
from app.uow import UnitOfWork, get_uow
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate
from app.services.categoria_service import CategoriaService

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


@router.get("", response_model=List[CategoriaRead])
def get_categorias(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    uow: UnitOfWork = Depends(get_uow)
):
    """Lista todas las categorías con paginación"""
    service = CategoriaService(uow)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{id}", response_model=CategoriaRead)
def get_categoria(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene una categoría por ID"""
    service = CategoriaService(uow)
    return service.get_by_id(id)


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def create_categoria(
    categoria_data: CategoriaCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Crea una nueva categoría"""
    service = CategoriaService(uow)
    return service.create(categoria_data)


@router.put("/{id}", response_model=CategoriaRead)
def update_categoria(
    id: Annotated[int, Path(gt=0)],
    categoria_data: CategoriaUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Actualiza una categoría existente"""
    service = CategoriaService(uow)
    return service.update(id, categoria_data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow)
):
    """Elimina una categoría"""
    service = CategoriaService(uow)
    service.delete(id)
