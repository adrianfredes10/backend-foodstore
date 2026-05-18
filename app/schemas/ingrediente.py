from datetime import datetime
from typing import List
from sqlmodel import SQLModel, Field


class IngredienteBase(SQLModel):
    """Base schema para Ingrediente"""
    nombre: str = Field(min_length=3, max_length=100)
    unidad_medida: str = Field(max_length=20)
    stock_actual: float = Field(ge=0)
    stock_minimo: float = Field(ge=0)


class IngredienteCreate(IngredienteBase):
    """Schema para crear un ingrediente"""
    pass


class IngredienteUpdate(IngredienteBase):
    """Schema para actualizar un ingrediente"""
    pass


class IngredienteRead(IngredienteBase):
    """Schema para leer un ingrediente"""
    id: int
    created_at: datetime


class IngredienteListResponse(SQLModel):
    """Respuesta paginada para ingredientes"""
    total: int
    items: List[IngredienteRead]
