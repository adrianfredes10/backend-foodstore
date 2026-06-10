# handlers de error en formato RFC 7807 (problem+json)
# se conserva el campo "detail" para no romper a los fronts
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

MEDIA_TYPE = "application/problem+json"
BASE_TYPE = "https://foodstore.local/errors/"

# status -> (slug para "type", "title")
_TITULOS: dict[int, tuple[str, str]] = {
    400: ("bad-request", "Bad Request"),
    401: ("unauthorized", "Unauthorized"),
    403: ("forbidden", "Forbidden"),
    404: ("not-found", "Not Found"),
    405: ("method-not-allowed", "Method Not Allowed"),
    409: ("conflict", "Conflict"),
    422: ("validation-error", "Unprocessable Entity"),
    429: ("rate-limit-exceeded", "Too Many Requests"),
    500: ("internal-error", "Internal Server Error"),
}


def _problem(
    *,
    status_code: int,
    detail: str,
    instance: str,
    extra: dict | None = None,
) -> JSONResponse:
    slug, title = _TITULOS.get(status_code, ("error", "Error"))
    body = {
        "type": BASE_TYPE + slug,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body, media_type=MEDIA_TYPE)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    resp = _problem(
        status_code=exc.status_code,
        detail=str(exc.detail),
        instance=request.url.path,
    )
    # respeta headers propios de la excepcion (ej: Retry-After, WWW-Authenticate)
    if exc.headers:
        for k, v in exc.headers.items():
            resp.headers[k] = v
    return resp


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errores = []
    for err in exc.errors():
        campo = ".".join(str(x) for x in err.get("loc", []))
        errores.append({"campo": campo, "mensaje": err.get("msg", "")})
    return _problem(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Los datos enviados no son validos",
        instance=request.url.path,
        extra={"errors": errores},
    )


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    # no exponemos el detalle de la base al cliente
    logger.warning("IntegrityError en %s: %s", request.url.path, str(exc.orig))
    return _problem(
        status_code=status.HTTP_409_CONFLICT,
        detail="La operacion viola una restriccion de integridad",
        instance=request.url.path,
    )


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error("SQLAlchemyError en %s: %r", request.url.path, exc, exc_info=True)
    return _problem(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error de base de datos",
        instance=request.url.path,
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.error("error no manejado en %s: %r", request.url.path, exc, exc_info=True)
    return _problem(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno del servidor",
        instance=request.url.path,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
