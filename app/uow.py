from sqlmodel import Session
from app.database import engine
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.ingrediente_repository import IngredienteRepository
from app.repositories.producto_repository import ProductoRepository


class UnitOfWork:
    """
    Controla la transacción de base de datos.
    Hace commit al salir sin errores, rollback ante cualquier excepción.
    Expone los repositories como atributos.
    """

    def __init__(self):
        self.session: Session = None

    def __enter__(self) -> "UnitOfWork":
        self.session = Session(engine)
        self.categorias = CategoriaRepository(self.session)
        self.ingredientes = IngredienteRepository(self.session)
        self.productos = ProductoRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    def flush(self):
        """Envía los cambios pendientes a la BD sin hacer commit."""
        self.session.flush()

    def refresh(self, instance):
        """Recarga el objeto desde la BD para leer relaciones actualizadas."""
        self.session.refresh(instance)


def get_uow() -> UnitOfWork:
    """Dependency para obtener un UnitOfWork. Para usar con Depends()."""
    return UnitOfWork()
