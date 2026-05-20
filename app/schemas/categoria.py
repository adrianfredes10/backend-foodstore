from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field


class CategoriaBase(SQLModel):
    nombre: str = Field(min_length=3, max_length=100)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = Field(default=None)


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(CategoriaBase):
    pass


class CategoriaSimple(SQLModel):
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    descripcion: Optional[str]
    parent_id: Optional[int]
    activa: bool


class CategoriaRead(SQLModel):
    model_config = {"from_attributes": True}

    id: int
    nombre: str
    descripcion: Optional[str]
    parent_id: Optional[int]
    activa: bool
    created_at: datetime
    subcategorias: List[CategoriaSimple] = Field(default_factory=list)
