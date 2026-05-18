from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class ProductoIngrediente(SQLModel, table=True):
    """Tabla intermedia para la relación N:N entre Producto e Ingrediente"""
    __tablename__ = "producto_ingrediente"
    
    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    ingrediente_id: int = Field(foreign_key="ingrediente.id", primary_key=True)
    cantidad: float = Field(gt=0, description="Cantidad del ingrediente en el producto")


class Ingrediente(SQLModel, table=True):
    """Modelo de Ingrediente"""
    __tablename__ = "ingrediente"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    # Unicidad efectiva solo para filas activas: índice parcial en migración SQL
    nombre: str = Field(min_length=3, max_length=100, index=True)
    unidad_medida: str = Field(max_length=20, description="Ej: ml, g, unidades")
    stock_actual: float = Field(ge=0, description="Stock disponible actual")
    stock_minimo: float = Field(ge=0, description="Stock mínimo requerido")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Relación N:N con Producto
    productos: List["Producto"] = Relationship(
        back_populates="ingredientes",
        link_model=ProductoIngrediente
    )
