from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.constants.codigos import RolCodigo
from app.core.auth_deps import require_roles
from app.models.seguridad import Usuario
from app.schemas.admin_schemas import (
    ListaUsuariosOut,
    UsuarioAdminUpdate,
    UsuarioRolesMutate,
)
from app.schemas.auth_schemas import UsuarioPublic
from app.services.admin_usuario_service import AdminUsuarioService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["admin-usuarios"])


@router.get("/usuarios", response_model=ListaUsuariosOut)
def listar_usuarios(
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
    rol: Annotated[Optional[str], Query(description="filtrar por código de rol")] = None,
):
    skip = (page - 1) * size
    return AdminUsuarioService(uow).listar(skip=skip, limit=size, rol_codigo=rol)


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioPublic)
def actualizar_usuario(
    usuario_id: Annotated[int, Path(gt=0)],
    body: UsuarioAdminUpdate,
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    return AdminUsuarioService(uow).actualizar(usuario_id, body)


@router.post("/usuarios/{usuario_id}/roles", response_model=UsuarioPublic)
def mutar_roles_usuario(
    usuario_id: Annotated[int, Path(gt=0)],
    body: UsuarioRolesMutate,
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    return AdminUsuarioService(uow).mutar_roles(usuario_id, body)


@router.delete("/usuarios/{usuario_id}/roles/{rol_codigo}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_rol(
    usuario_id: Annotated[int, Path(gt=0)],
    rol_codigo: str,
    _admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    AdminUsuarioService(uow).quitar_rol(usuario_id, rol_codigo)


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: Annotated[int, Path(gt=0)],
    admin: Annotated[Usuario, Depends(require_roles(RolCodigo.ADMIN))],
    uow: UnitOfWork = Depends(get_uow),
):
    AdminUsuarioService(uow).eliminar(usuario_id, admin.id)
