from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship
from app.models.ingrediente import Ingrediente, ProductoIngrediente


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=3, max_length=150, index=True)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    disponible: bool = Field(default=True)
    stock_cantidad: float = Field(default=0, ge=0)
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    # public_id de Cloudinary (para reemplazar/borrar la imagen principal)
    imagen_public_id: Optional[str] = Field(default=None, max_length=255)
    # array de imagenes: [{"url": "...", "public_id": "..."}] (spec v7)
    imagenes_data: Optional[list] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    # 1:N con categoria
    categoria_id: int = Field(foreign_key="categoria.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    categoria: Optional["Categoria"] = Relationship(back_populates="productos")

    ingredientes: List[Ingrediente] = Relationship(
        back_populates="productos",
        link_model=ProductoIngrediente,
    )
