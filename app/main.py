import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import RateLimitMiddleware
from app.core.timing_middleware import TimingMiddleware
from app.database import create_db_and_tables
from app.routers import (
    admin_usuarios_v1_router,
    catalogos_router,
    categorias_router,
    direcciones_v1_router,
    ingredientes_router,
    pedidos_v1_router,
    productos_router,
)
from app.routers.estadisticas import router as estadisticas_router
from app.routers.uploads import router as uploads_router
from app.routers.v1.auth import router as auth_v1_router
from app.routers.v1.pagos import router as pagos_v1_router
from app.routers.ws import router as ws_router
from app.seed_obligatorio import run_seed_obligatorio

app = FastAPI(
    title="FoodStore API",
    description="Backend para sistema de pedidos de comida",
    version="1.0.0",
)

settings = get_settings()

# logs de app.* visibles en consola (timing, errores, ws, pagos)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
)
# silencia el spam de sqlalchemy para ver los logs de timing
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# orden middlewares (ultimo agregado = primero en ejecutar):
# timing mide el round-trip completo; rate limit solo en auth
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TimingMiddleware)

# handlers de error en formato RFC 7807
register_exception_handlers(app)

app.include_router(auth_v1_router, prefix="/api/v1/auth")
app.include_router(categorias_router, prefix="/api/v1/categorias")
app.include_router(ingredientes_router, prefix="/api/v1/ingredientes")
app.include_router(productos_router, prefix="/api/v1/productos")
app.include_router(direcciones_v1_router, prefix="/api/v1/direcciones")
app.include_router(pedidos_v1_router, prefix="/api/v1/pedidos")
app.include_router(admin_usuarios_v1_router, prefix="/api/v1/admin")
app.include_router(pagos_v1_router, prefix="/api/v1/pagos")
app.include_router(uploads_router, prefix="/api/v1/uploads")
app.include_router(estadisticas_router, prefix="/api/v1/estadisticas")
app.include_router(catalogos_router, prefix="/api/v1")
app.include_router(ws_router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    run_seed_obligatorio()


@app.get("/")
def root():
    return {
        "message": "FoodStore API",
        "version": "1.0.0",
        "docs": "/docs",
    }
