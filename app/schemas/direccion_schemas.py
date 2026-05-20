from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class DireccionCreate(SQLModel):
    alias: str = Field(max_length=80)
    calle: str = Field(max_length=200)
    numero: str = Field(max_length=20)
    referencia: Optional[str] = Field(default=None, max_length=300)
    ciudad: str = Field(max_length=120)
    codigo_postal: Optional[str] = Field(default=None, max_length=20)
    es_principal: bool = False


class DireccionUpdate(SQLModel):
    alias: Optional[str] = Field(default=None, max_length=80)
    calle: Optional[str] = Field(default=None, max_length=200)
    numero: Optional[str] = Field(default=None, max_length=20)
    referencia: Optional[str] = Field(default=None, max_length=300)
    ciudad: Optional[str] = Field(default=None, max_length=120)
    codigo_postal: Optional[str] = Field(default=None, max_length=20)


class DireccionRead(SQLModel):
    id: int
    usuario_id: int
    alias: str
    calle: str
    numero: str
    referencia: Optional[str]
    ciudad: str
    codigo_postal: Optional[str]
    es_principal: bool
    created_at: datetime
