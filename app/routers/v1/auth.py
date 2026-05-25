from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.deps.auth_deps import COOKIE_NAME, get_current_user
from app.models.seguridad import Usuario
from app.schemas.auth_schemas import LoginRequest, RegistroRequest, UsuarioPublic
from app.services.auth_service import AuthService, _to_public
from app.uow import UnitOfWork, get_uow

router = APIRouter()


@router.post("/register", response_model=UsuarioPublic, status_code=status.HTTP_201_CREATED)
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
    user_public, token = svc.login(body.email, body.password)
    settings = get_settings()
    resp = JSONResponse(content=user_public.model_dump(mode="json"))
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,
        path="/",
    )
    return resp


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=UsuarioPublic)
def obtener_perfil_actual(user: Annotated[Usuario, Depends(get_current_user)]):
    # user viene de get_current_user con roles cargados en la sesión activa
    # la sesión de auth_deps se cierra sin commit, así que los atributos no expiran
    return _to_public(user)
