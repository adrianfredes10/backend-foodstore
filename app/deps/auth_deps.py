from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import decode_access_token
from app.database import engine
from app.models.seguridad import Usuario

COOKIE_NAME = "access_token"


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
        # forzar la carga de roles mientras la sesión sigue abierta
        _ = [r.codigo for r in usuario.roles]
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
