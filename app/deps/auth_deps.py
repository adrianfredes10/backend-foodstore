from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.core.security import decode_access_token
from app.database import engine
from app.models.seguridad import Usuario

COOKIE_NAME = "access_token"


def get_current_user_optional(
    access_token: Annotated[Optional[str], Cookie(alias=COOKIE_NAME)] = None,
) -> Optional[Usuario]:
    if not access_token:
        return None
    try:
        payload = decode_access_token(access_token)
    except Exception:
        return None
    uid = payload.get("uid")
    if not uid:
        return None
    with Session(engine) as session:
        usuario = session.exec(
            select(Usuario)
            .where(Usuario.id == int(uid), Usuario.deleted_at.is_(None))
            .options(selectinload(Usuario.roles))
        ).first()
        if not usuario or not usuario.activo:
            return None
        return usuario


def get_current_user(
    user: Annotated[Optional[Usuario], Depends(get_current_user_optional)],
) -> Usuario:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )
    return user


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
