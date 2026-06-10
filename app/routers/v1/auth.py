from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.auth_deps import (
    COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    get_current_user,
)
from app.models.seguridad import Usuario
from app.schemas.auth_schemas import LoginRequest, RegistroRequest, UsuarioPublic
from app.services.auth_service import AuthService, _to_public
from app.uow import UnitOfWork, get_uow

router = APIRouter()


def _set_access_cookie(resp: Response, token: str) -> None:
    s = get_settings()
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=s.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,
        path="/",
    )


def _set_refresh_cookie(resp: Response, token: str) -> None:
    s = get_settings()
    resp.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=s.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=False,
        path=REFRESH_COOKIE_PATH,
    )


@router.post(
    "/register", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED
)
def registrar(
    body: RegistroRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    svc = AuthService(uow)
    return svc.register(
        body.email,
        body.password,
        body.nombre,
        body.apellido,
        body.telefono,
    )


@router.post("/login", response_model=UsuarioPublic)
def login(
    body: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    svc = AuthService(uow)
    user_public, access, refresh = svc.login(body.email, body.password)
    resp = JSONResponse(content=user_public.model_dump(mode="json"))
    _set_access_cookie(resp, access)
    _set_refresh_cookie(resp, refresh)
    return resp


@router.post("/refresh", response_model=UsuarioPublic)
def refresh(
    refresh_token: Annotated[Optional[str], Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    uow: UnitOfWork = Depends(get_uow),
):
    from fastapi import HTTPException, status as http_status
    if not refresh_token:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ausente",
        )
    svc = AuthService(uow)
    user_public, access, nuevo_refresh = svc.refresh(refresh_token)
    resp = JSONResponse(content=user_public.model_dump(mode="json"))
    _set_access_cookie(resp, access)
    _set_refresh_cookie(resp, nuevo_refresh)
    return resp


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: Annotated[Usuario, Depends(get_current_user)],
    refresh_token: Annotated[Optional[str], Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    uow: UnitOfWork = Depends(get_uow),
):
    svc = AuthService(uow)
    svc.logout(refresh_token)
    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie(COOKIE_NAME, path="/")
    resp.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return resp


@router.get("/me", response_model=UsuarioPublic)
def obtener_perfil_actual(user: Annotated[Usuario, Depends(get_current_user)]):
    # user viene de get_current_user con roles cargados en la sesion activa
    return _to_public(user)
