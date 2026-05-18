from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class ProductoCategoria(SQLModel, table=True):
    """Tabla intermedia para la relación N:N entre Producto y Categoría"""
    __tablename__ = "producto_categoria"

    producto_id: int = Field(foreign_key="producto.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categoria.id", primary_key=True)


class Categoria(SQLModel, table=True):
    """Modelo de Categoría con soporte de jerarquía (subcategorías)."""
    __tablename__ = "categoria"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(min_length=3, max_length=100, index=True)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="categoria.id",
        nullable=True,
    )

    subcategorias: List["Categoria"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "foreign_keys": "[Categoria.parent_id]",
            "lazy": "selectin",
        },
    )
    parent: Optional["Categoria"] = Relationship(
        back_populates="subcategorias",
        sa_relationship_kwargs={
            "foreign_keys": "[Categoria.parent_id]",
            "remote_side": "[Categoria.id]",
        },
    )

    productos: List["Producto"] = Relationship(
        back_populates="categorias",
        link_model=ProductoCategoria,
    )
