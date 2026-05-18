from typing import Annotated, List
from fastapi import APIRouter, Query, Path, status, Depends
from app.uow import UnitOfWork, get_uow
from app.schemas.ingrediente import IngredienteCreate, IngredienteRead, IngredienteUpdate
from app.services.ingrediente_service import IngredienteService

router = APIRouter(prefix="/api/ingredientes", tags=["ingredientes"])


@router.get("", response_model=List[IngredienteRead])
def get_ingredientes(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    uow: UnitOfWork = Depends(get_uow)
):
    """Lista todos los ingredientes con paginación"""
    service = IngredienteService(uow)
    return service.get_all(skip=skip, limit=limit)


@router.get("/{id}", response_model=IngredienteRead)
def get_ingrediente(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow)
):
    """Obtiene un ingrediente por ID"""
    service = IngredienteService(uow)
    return service.get_by_id(id)


@router.post("", response_model=IngredienteRead, status_code=status.HTTP_201_CREATED)
def create_ingrediente(
    ingrediente_data: IngredienteCreate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Crea un nuevo ingrediente"""
    service = IngredienteService(uow)
    return service.create(ingrediente_data)


@router.put("/{id}", response_model=IngredienteRead)
def update_ingrediente(
    id: Annotated[int, Path(gt=0)],
    ingrediente_data: IngredienteUpdate,
    uow: UnitOfWork = Depends(get_uow)
):
    """Actualiza un ingrediente existente"""
    service = IngredienteService(uow)
    return service.update(id, ingrediente_data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingrediente(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow)
):
    """Elimina un ingrediente"""
    service = IngredienteService(uow)
    service.delete(id)
