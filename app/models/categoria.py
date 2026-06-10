from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=3, max_length=100, index=True)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    activa: bool = Field(default=True)
    # url de Cloudinary (v7); se setea via modulo /uploads
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="categoria.id",
        nullable=True,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    subcategorias: List["Categoria"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"foreign_keys": "[Categoria.parent_id]"},
    )
    parent: Optional["Categoria"] = Relationship(
        back_populates="subcategorias",
        sa_relationship_kwargs={
            "foreign_keys": "[Categoria.parent_id]",
            "remote_side": "[Categoria.id]",
        },
    )

    # relación 1:N hacia productos (un producto tiene una sola categoría)
    productos: List["Producto"] = Relationship(back_populates="categoria")
