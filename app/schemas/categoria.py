from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field


class CategoriaBase(SQLModel):
    """Base schema para Categoría"""
    nombre: str = Field(min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = Field(
        default=None,
        description="ID de la categoría padre. None = categoría raíz.",
    )


class CategoriaCreate(CategoriaBase):
    """Schema para crear una categoría. parent_id opcional."""
    pass


class CategoriaUpdate(CategoriaBase):
    """Schema para actualizar una categoría."""
    pass


class CategoriaSimple(SQLModel):
    """Subcategoría en respuesta sin anidar más niveles (evita recursión)."""
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    descripcion: Optional[str]
    parent_id: Optional[int]


class CategoriaRead(SQLModel):
    """Schema de salida para una categoría (un nivel de subcategorías)."""
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    descripcion: Optional[str]
    parent_id: Optional[int]
    created_at: datetime
    subcategorias: List[CategoriaSimple] = Field(default_factory=list)


class CategoriaListResponse(SQLModel):
    """Respuesta paginada para categorías"""
    total: int
    items: List[CategoriaRead]
