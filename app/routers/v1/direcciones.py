from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, status

from app.deps.auth_deps import get_current_user
from app.models.seguridad import Usuario
from app.schemas.direccion_schemas import DireccionCreate, DireccionRead, DireccionUpdate
from app.services.direccion_service import DireccionService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["direcciones"])


@router.get("", response_model=List[DireccionRead])
def listar(
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return DireccionService(uow).listar(user.id)


@router.post("", response_model=DireccionRead, status_code=status.HTTP_201_CREATED)
def crear(
    body: DireccionCreate,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return DireccionService(uow).crear(user.id, body)


@router.patch("/{direccion_id}", response_model=DireccionRead)
def actualizar(
    direccion_id: Annotated[int, Path(gt=0)],
    body: DireccionUpdate,
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return DireccionService(uow).actualizar(user.id, direccion_id, body)


@router.patch("/{direccion_id}/principal", response_model=DireccionRead)
def marcar_principal(
    direccion_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    return DireccionService(uow).marcar_principal(user.id, direccion_id)


@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    direccion_id: Annotated[int, Path(gt=0)],
    user: Annotated[Usuario, Depends(get_current_user)],
    uow: UnitOfWork = Depends(get_uow),
):
    DireccionService(uow).eliminar(user.id, direccion_id)
    return None
