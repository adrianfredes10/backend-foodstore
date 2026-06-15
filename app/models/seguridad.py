# usuario <-> rol por tabla usuario_rol
from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"

    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    rol_id: int = Field(foreign_key="rol.id", primary_key=True)
    fecha_asignacion: datetime = Field(default_factory=datetime.utcnow)
    # v7: vencimiento opcional de la asignacion de rol (D-05)
    expires_at: Optional[datetime] = Field(default=None)


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True, index=True, max_length=32)
    nombre: str = Field(max_length=120)

    usuarios: List["Usuario"] = Relationship(
        back_populates="roles",
        link_model=UsuarioRol,
    )


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    nombre: str = Field(max_length=120)
    apellido: str = Field(max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=30)
    celular: Optional[str] = Field(default=None, max_length=20)
    activo: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    roles: List["Rol"] = Relationship(
        back_populates="usuarios",
        link_model=UsuarioRol,
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    # se guarda el hash sha256 del token, nunca el valor plano
    token_hash: str = Field(unique=True, index=True, max_length=64)
    expires_at: datetime
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
