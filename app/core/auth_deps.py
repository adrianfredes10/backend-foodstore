from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import decode_access_token
from app.database import engine
from app.models.seguridad import Usuario, UsuarioRol

COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
# la cookie de refresh solo viaja a los endpoints de auth
REFRESH_COOKIE_PATH = "/api/v1/auth"


def get_current_user(
    access_token: Annotated[Optional[str], Cookie(alias=COOKIE_NAME)] = None,
) -> Usuario:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    uid = payload.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    with Session(engine) as session:
        usuario = session.exec(
            select(Usuario)
            .where(Usuario.id == int(uid), Usuario.deleted_at.is_(None))
        ).first()
        if not usuario or not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inválido o inactivo",
            )
        # filtrar roles vencidos (D-05: expires_at en UsuarioRol)
        now = datetime.now(timezone.utc)
        ur_rows = session.exec(
            select(UsuarioRol).where(UsuarioRol.usuario_id == int(uid))
        ).all()
        rol_ids_vigentes: set[int] = set()
        for ur in ur_rows:
            exp = ur.expires_at
            if exp is None:
                rol_ids_vigentes.add(ur.rol_id)
            else:
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp > now:
                    rol_ids_vigentes.add(ur.rol_id)
        # reemplazar la lista de roles con solo los vigentes
        usuario.roles = [r for r in usuario.roles if r.id in rol_ids_vigentes]
        return usuario


def require_roles(*codigos: str):
    def _dep(user: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
        tiene = {r.codigo for r in user.roles}
        if not tiene.intersection(set(codigos)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return _dep
