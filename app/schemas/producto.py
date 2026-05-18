from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import field_validator, field_serializer
from sqlmodel import SQLModel, Field
from app.schemas.categoria import CategoriaRead


class ProductoIngredienteInput(SQLModel):
    """Schema para asignar ingredientes a un producto"""
    ingrediente_id: int
    cantidad: float = Field(gt=0)


class ProductoIngredienteRead(SQLModel):
    """Schema para leer ingredientes de un producto"""
    ingrediente_id: int
    nombre: str
    cantidad: float
    unidad_medida: str


class ProductoBase(SQLModel):
    """Base schema para Producto"""
    nombre: str = Field(min_length=3, max_length=150)
    descripcion: Optional[str] = Field(default=None, max_length=1000)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    disponible: bool = Field(default=True)


class ProductoCreate(ProductoBase):
    """Schema para crear un producto"""
    categoria_ids: List[int] = Field(min_length=1)
    ingredientes: List[ProductoIngredienteInput] = Field(min_length=1)


class ProductoUpdate(ProductoBase):
    """Schema para actualizar un producto"""
    categoria_ids: List[int] = Field(min_length=1)
    ingredientes: List[ProductoIngredienteInput] = Field(min_length=1)


class ProductoRead(ProductoBase):
    """Schema para leer un producto con todas sus relaciones"""
    id: int
    created_at: datetime
    categorias: List[CategoriaRead]
    ingredientes: List[ProductoIngredienteRead]

    @field_serializer('precio')
    def serialize_precio(self, v: Decimal) -> float:
        """Serializa Decimal a float para JSON"""
        return float(v)
