# una direccion por usuario soft deleted_at
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direccion_entrega"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    alias: str = Field(max_length=80)
    calle: str = Field(max_length=200)
    numero: str = Field(max_length=20)
    referencia: Optional[str] = Field(default=None, max_length=300)
    ciudad: str = Field(max_length=120)
    codigo_postal: Optional[str] = Field(default=None, max_length=20)
    es_principal: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)
