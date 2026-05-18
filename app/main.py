from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
from app.database import create_db_and_tables
from app.routers import categorias_router, ingredientes_router, productos_router

# Crear aplicación FastAPI
app = FastAPI(
    title="Parcial Prog4 API",
    description="API para gestión de productos, categorías e ingredientes",
    version="1.0.0"
)

# Configurar CORS para permitir requests desde frontend (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL del frontend en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(categorias_router)
app.include_router(ingredientes_router)
app.include_router(productos_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura cualquier error no manejado y muestra el detalle"""
    error_detail = traceback.format_exc()
    print("❌ ERROR NO MANEJADO:")
    print(error_detail)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": error_detail}
    )


@app.on_event("startup")
def on_startup():
    """Crear tablas en la base de datos al iniciar"""
    create_db_and_tables()


@app.get("/")
def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {
        "message": "Parcial Prog4 API",
        "version": "1.0.0",
        "docs": "/docs"
    }
