from fastapi import HTTPException, status

from app.constants.codigos import RolCodigo
from app.core.security import (
    create_access_token,
    generar_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_expira_en,
    verify_password,
)
from app.models.seguridad import Usuario
from app.schemas.auth_schemas import PerfilUpdate, RolPublic, UsuarioPublic
from app.uow import UnitOfWork


def _to_public(u: Usuario) -> UsuarioPublic:
    # serializa dentro de la sesion activa para evitar DetachedInstanceError
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


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def register(
        self,
        email: str,
        password: str,
        nombre: str,
        apellido: str,
        telefono: str | None = None,
    ) -> UsuarioPublic:
        with self.uow as uow:
            if uow.usuarios.get_by_email(email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya está registrado",
                )
            rol_client = uow.roles.get_by_codigo(RolCodigo.CLIENT)
            if not rol_client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Rol CLIENT no configurado (corre el seed)",
                )
            user = Usuario(
                email=email,
                password_hash=hash_password(password),
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
            )
            uow.usuarios.create(user)
            uow.usuarios.add_rol(user.id, rol_client.id)
            uow.flush()
            reloaded = uow.usuarios.get_by_id(user.id)
            if not reloaded:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error al crear usuario",
                )
            return _to_public(reloaded)

    def actualizar_perfil(self, usuario_id: int, data: PerfilUpdate) -> UsuarioPublic:
        with self.uow as uow:
            user = uow.usuarios.get_by_id(usuario_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )
            patch = data.model_dump(exclude_unset=True)
            if patch:
                uow.usuarios.update_fields(user, **patch)
                uow.flush()
                uow.refresh(user)
                _ = [r.codigo for r in user.roles]
            return _to_public(user)

    def login(self, email: str, password: str) -> tuple[UsuarioPublic, str, str]:
        with self.uow as uow:
            user = uow.usuarios.get_by_email(email)
            if not user or not verify_password(password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email o contraseña incorrectos",
                )
            if not user.activo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cuenta desactivada",
                )
            roles = [r.codigo for r in user.roles]
            access = create_access_token(
                subject_email=user.email,
                user_id=user.id,
                roles=roles,
            )
            refresh_plano = self._emitir_refresh(uow, user.id)
            return _to_public(user), access, refresh_plano

    def refresh(self, refresh_plano: str) -> tuple[UsuarioPublic, str, str]:
        with self.uow as uow:
            rt = uow.refresh_tokens.get_valido(hash_refresh_token(refresh_plano))
            if not rt:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token invalido o expirado",
                )
            user = uow.usuarios.get_by_id(rt.usuario_id)
            if not user or not user.activo:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario invalido o inactivo",
                )
            # rotacion: se revoca el viejo y se emite uno nuevo
            uow.refresh_tokens.revoke(rt)
            roles = [r.codigo for r in user.roles]
            access = create_access_token(
                subject_email=user.email,
                user_id=user.id,
                roles=roles,
            )
            nuevo_refresh = self._emitir_refresh(uow, user.id)
            return _to_public(user), access, nuevo_refresh

    def logout(self, refresh_plano: str | None) -> None:
        if not refresh_plano:
            return
        with self.uow as uow:
            uow.refresh_tokens.revoke_by_hash(hash_refresh_token(refresh_plano))

    @staticmethod
    def _emitir_refresh(uow: UnitOfWork, usuario_id: int) -> str:
        plano = generar_refresh_token()
        uow.refresh_tokens.create(
            usuario_id=usuario_id,
            token_hash=hash_refresh_token(plano),
            expires_at=refresh_expira_en(),
        )
        return plano
