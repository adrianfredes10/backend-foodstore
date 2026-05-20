from typing import Optional

from fastapi import HTTPException, status

from app.schemas.admin_schemas import (
    ListaUsuariosOut,
    UsuarioAdminUpdate,
    UsuarioRolesMutate,
)
from app.schemas.auth_schemas import RolPublic, UsuarioPublic
from app.uow import UnitOfWork


class AdminUsuarioService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @staticmethod
    def _public(u) -> UsuarioPublic:
        return UsuarioPublic(
            id=u.id,
            email=u.email,
            nombre=u.nombre,
            apellido=u.apellido,
            telefono=u.telefono,
            activo=u.activo,
            roles=[
                RolPublic(id=r.id, codigo=r.codigo, nombre=r.nombre)
                for r in (u.roles or [])
            ],
        )

    def listar(
        self,
        *,
        skip: int,
        limit: int,
        rol_codigo: Optional[str],
    ) -> ListaUsuariosOut:
        with self.uow as uow:
            total = uow.usuarios.count_filtrado(rol_codigo)
            items = uow.usuarios.list_paginado(skip, limit, rol_codigo)
            return ListaUsuariosOut(
                total=total,
                items=[self._public(x) for x in items],
            )

    def actualizar(self, usuario_id: int, data: UsuarioAdminUpdate) -> UsuarioPublic:
        with self.uow as uow:
            u = uow.usuarios.get_by_id(usuario_id)
            if not u:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            if data.activo is not None:
                u.activo = data.activo
                uow.session.add(u)
            if data.roles_codigos is not None:
                vistos: set[int] = set()
                rol_ids: list[int] = []
                for cod in data.roles_codigos:
                    rol = uow.roles.get_by_codigo(cod)
                    if not rol:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Rol '{cod}' no existe",
                        )
                    if rol.id not in vistos:
                        vistos.add(rol.id)
                        rol_ids.append(rol.id)
                uow.usuarios.clear_roles(usuario_id)
                for rid in rol_ids:
                    uow.usuarios.add_rol(usuario_id, rid)
            uow.flush()
            u2 = uow.usuarios.get_by_id(usuario_id)
            return self._public(u2)

    def mutar_roles(self, usuario_id: int, body: UsuarioRolesMutate) -> UsuarioPublic:
        # primero quitar despues agregar (mismo codigo en ambas listas queda asignado)
        quitar = body.quitar or []
        agregar = body.agregar or []
        with self.uow as uow:
            u = uow.usuarios.get_by_id(usuario_id)
            if not u:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            for cod in quitar:
                rol = uow.roles.get_by_codigo(cod)
                if not rol:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Rol '{cod}' no existe",
                    )
                uow.usuarios.remove_rol(usuario_id, rol.id)
            for cod in agregar:
                rol = uow.roles.get_by_codigo(cod)
                if not rol:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Rol '{cod}' no existe",
                    )
                uow.usuarios.add_rol(usuario_id, rol.id)
            uow.flush()
            u2 = uow.usuarios.get_by_id(usuario_id)
            return self._public(u2)

    def quitar_rol(self, usuario_id: int, rol_codigo: str) -> None:
        with self.uow as uow:
            u = uow.usuarios.get_by_id(usuario_id)
            if not u:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            rol = uow.roles.get_by_codigo(rol_codigo)
            if not rol:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rol '{rol_codigo}' no existe",
                )
            uow.usuarios.remove_rol(usuario_id, rol.id)

    def eliminar(self, usuario_id: int, actor_id: int) -> None:
        if usuario_id == actor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No podés dar de baja tu propio usuario",
            )
        with self.uow as uow:
            u = uow.usuarios.get_by_id(usuario_id)
            if not u:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            uow.usuarios.soft_delete(u)
