from typing import List, Optional

from pydantic import Field, model_validator
from sqlmodel import SQLModel

from app.schemas.auth_schemas import UsuarioPublic


class UsuarioAdminUpdate(SQLModel):
    activo: Optional[bool] = None
    roles_codigos: Optional[List[str]] = Field(
        default=None,
        description="si viene, reemplaza todos los roles del usuario",
    )


class UsuarioRolesMutate(SQLModel):
    agregar: Optional[List[str]] = Field(
        default=None,
        description="codigos de rol a agregar sin pisar el resto",
    )
    quitar: Optional[List[str]] = Field(
        default=None,
        description="codigos de rol a sacar",
    )

    @model_validator(mode="after")
    def _alguna_lista(self) -> "UsuarioRolesMutate":
        a = self.agregar or []
        q = self.quitar or []
        if not a and not q:
            raise ValueError("mandá al menos agregar o quitar con un rol")
        return self


class ListaUsuariosOut(SQLModel):
    total: int
    items: List[UsuarioPublic]
