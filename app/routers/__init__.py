from app.routers.catalogos import router as catalogos_router
from app.routers.categorias import router as categorias_router
from app.routers.ingredientes import router as ingredientes_router
from app.routers.productos import router as productos_router
from app.routers.v1.admin_usuarios import router as admin_usuarios_v1_router
from app.routers.v1.direcciones import router as direcciones_v1_router
from app.routers.v1.pedidos import router as pedidos_v1_router

__all__ = [
    "catalogos_router",
    "categorias_router",
    "ingredientes_router",
    "productos_router",
    "direcciones_v1_router",
    "pedidos_v1_router",
    "admin_usuarios_v1_router",
]
