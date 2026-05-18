from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship
from app.models.categoria import Categoria, ProductoCategoria
from app.models.ingrediente import Ingrediente, ProductoIngrediente


class Producto(SQLModel, table=True):
    """Modelo de Producto"""
    __tablename__ = "producto"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    # Unicidad efectiva solo para filas activas: índice parcial en migración SQL
    nombre: str = Field(min_length=3, max_length=150, index=True)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    disponible: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Relación N:N con Categoría
    categorias: List[Categoria] = Relationship(
        back_populates="productos",
        link_model=ProductoCategoria
    )
    
    # Relación N:N con Ingrediente
    ingredientes: List[Ingrediente] = Relationship(
        back_populates="productos",
        link_model=ProductoIngrediente
    )
