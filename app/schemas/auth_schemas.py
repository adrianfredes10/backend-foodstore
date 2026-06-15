from typing import List, Optional

from pydantic import EmailStr, Field
from sqlmodel import SQLModel


class RolPublic(SQLModel):
    id: int
    codigo: str
    nombre: str


class UsuarioPublic(SQLModel):
    id: int
    email: str
    nombre: str
    apellido: str
    telefono: Optional[str]
    activo: bool
    roles: List[RolPublic] = Field(default_factory=list)


class RegistroRequest(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=2, max_length=120)
    apellido: str = Field(min_length=2, max_length=120)
    telefono: Optional[str] = None


class LoginRequest(SQLModel):
    email: str
    password: str


class PerfilUpdate(SQLModel):
    # edicion del propio perfil (cliente): solo datos personales, no email/password/roles
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=120)
    apellido: Optional[str] = Field(default=None, min_length=2, max_length=120)
    telefono: Optional[str] = Field(default=None, max_length=30)
