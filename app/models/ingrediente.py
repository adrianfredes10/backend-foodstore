from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    ingrediente_id: int = Field(foreign_key="ingrediente.id", primary_key=True)
    cantidad: float = Field(gt=0)
    # alergeno especifico de esta combinacion producto-ingrediente
    es_alergeno: bool = Field(default=False)


class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingrediente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=3, max_length=100, index=True)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    es_alergeno: bool = Field(default=False)
    # string legible (contrato actual) + FK opcional a la entidad v7 (D-02)
    unidad_medida: str = Field(max_length=20)
    unidad_medida_id: Optional[int] = Field(
        default=None, foreign_key="unidad_medida.id"
    )
    stock_actual: float = Field(ge=0)
    stock_minimo: float = Field(ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    productos: List["Producto"] = Relationship(
        back_populates="ingredientes",
        link_model=ProductoIngrediente,
    )
