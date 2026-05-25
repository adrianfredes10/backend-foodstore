import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
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
from app.routers.v1.auth import router as auth_v1_router
from app.seed_obligatorio import run_seed_obligatorio

app = FastAPI(
    title="FoodStore API",
    description="Backend para sistema de pedidos de comida",
    version="1.0.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_v1_router, prefix="/api/v1/auth")
app.include_router(categorias_router, prefix="/api/v1/categorias")
app.include_router(ingredientes_router, prefix="/api/v1/ingredientes")
app.include_router(productos_router, prefix="/api/v1/productos")
app.include_router(direcciones_v1_router, prefix="/api/v1/direcciones")
app.include_router(pedidos_v1_router, prefix="/api/v1/pedidos")
app.include_router(admin_usuarios_v1_router, prefix="/api/v1/admin")
app.include_router(catalogos_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error("error no manejado: %s\n%s", exc, traceback.format_exc())
    # no mandar traceback al cliente
    return JSONResponse(status_code=500, content={"detail": str(exc)})


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
