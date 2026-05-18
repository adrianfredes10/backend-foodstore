from app.routers.categorias import router as categorias_router
from app.routers.ingredientes import router as ingredientes_router
from app.routers.productos import router as productos_router

__all__ = [
    "categorias_router",
    "ingredientes_router",
    "productos_router",
]
