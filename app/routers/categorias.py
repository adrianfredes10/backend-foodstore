from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.constants.codigos import RolCodigo
from app.deps.auth_deps import require_roles
from app.models.seguridad import Usuario
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate
from app.schemas.common import PaginatedResponse
from app.services.categoria_service import CategoriaService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["categorias"])


@router.get("", response_model=PaginatedResponse)
def get_categorias(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    parent_id: Annotated[Optional[int], Query()] = None,
    activa: Annotated[Optional[bool], Query()] = True,
    recursivo: Annotated[bool, Query()] = False,
    uow: UnitOfWork = Depends(get_uow),
):
    return CategoriaService(uow).get_all(
        page=page,
        size=size,
        parent_id=parent_id,
        activa=activa,
        recursivo=recursivo,
    )


@router.get("/{id}", response_model=CategoriaRead)
def get_categoria(
    id: Annotated[int, Path(gt=0)],
    uow: UnitOfWork = Depends(get_uow),
):
    return CategoriaService(uow).get_by_id(id)


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def create_categoria(
    categoria_data: CategoriaCreate,
    *,
    uow: UnitOfWork = Depends(get_uow),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
):
    return CategoriaService(uow).create(categoria_data)


@router.put("/{id}", response_model=CategoriaRead)
def update_categoria(
    id: Annotated[int, Path(gt=0)],
    categoria_data: CategoriaUpdate,
    *,
    uow: UnitOfWork = Depends(get_uow),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
):
    return CategoriaService(uow).update(id, categoria_data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    id: Annotated[int, Path(gt=0)],
    *,
    uow: UnitOfWork = Depends(get_uow),
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
):
    CategoriaService(uow).delete(id)
