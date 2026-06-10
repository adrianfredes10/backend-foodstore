from sqlmodel import Session
from app.database import engine
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.ingrediente_repository import IngredienteRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.rol_repository import RolRepository
from app.repositories.direccion_repository import DireccionRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.usuario_repository import UsuarioRepository


class UnitOfWork:
    # commit ok rollback si falla repos con el mismo session

    def __init__(self):
        self.session: Session = None

    def __enter__(self) -> "UnitOfWork":
        # expire_on_commit=False: los objetos siguen usables tras el commit
        # (evita DetachedInstanceError al serializar fuera del with)
        self.session = Session(engine, expire_on_commit=False)
        self.categorias = CategoriaRepository(self.session)
        self.ingredientes = IngredienteRepository(self.session)
        self.productos = ProductoRepository(self.session)
        self.roles = RolRepository(self.session)
        self.usuarios = UsuarioRepository(self.session)
        self.pedidos = PedidoRepository(self.session)
        self.direcciones = DireccionRepository(self.session)
        self.refresh_tokens = RefreshTokenRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    def flush(self):
        # flush sin commit (ver __exit__)
        self.session.flush()

    def refresh(self, instance):
        # relee el objeto por si cambio en bd
        self.session.refresh(instance)


def get_uow() -> UnitOfWork:
    # factory para Depends(get_uow)
    return UnitOfWork()
