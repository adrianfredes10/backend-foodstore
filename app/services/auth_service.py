from fastapi import HTTPException, status

from app.constants.codigos import RolCodigo
from app.core.security import hash_password, verify_password, create_access_token
from app.models.seguridad import Usuario
from app.schemas.auth_schemas import RolPublic, UsuarioPublic
from app.uow import UnitOfWork


def _to_public(u: Usuario) -> UsuarioPublic:
    # serializa dentro de la sesión activa para evitar DetachedInstanceError
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

    def login(self, email: str, password: str) -> tuple[UsuarioPublic, str]:
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
            token = create_access_token(
                subject_email=user.email,
                user_id=user.id,
                roles=roles,
            )
            return _to_public(user), token
