from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import field_serializer
from sqlmodel import SQLModel, Field
from app.schemas.categoria import CategoriaRead


class ProductoIngredienteInput(SQLModel):
    ingrediente_id: int
    cantidad: float = Field(gt=0)
    es_alergeno: bool = False


class ProductoIngredienteRead(SQLModel):
    ingrediente_id: int
    nombre: str
    cantidad: float
    unidad_medida: str
    es_alergeno: bool = False


class ProductoBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    disponible: bool = Field(default=True)
    stock_cantidad: float = Field(ge=0, default=0)
    imagen_url: Optional[str] = Field(default=None, max_length=500)


class ProductoCreate(ProductoBase):
    # 1:N — un solo id de categoría
    categoria_id: int
    ingredientes: List[ProductoIngredienteInput] = Field(min_length=1)


class ProductoUpdate(ProductoBase):
    categoria_id: int
    ingredientes: List[ProductoIngredienteInput] = Field(min_length=1)


class ProductoDisponibilidadBody(SQLModel):
    disponible: bool


class ProductoStockBody(SQLModel):
    stock_cantidad: float = Field(ge=0)


class ProductoRead(ProductoBase):
    id: int
    created_at: datetime
    # objeto único, no lista
    categoria: Optional[CategoriaRead]
    ingredientes: List[ProductoIngredienteRead]

    @field_serializer("precio")
    def serialize_precio(self, v: Decimal) -> str:
        # string para evitar problemas de precisión en js
        return str(v)
