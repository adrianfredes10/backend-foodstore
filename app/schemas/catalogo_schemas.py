from sqlmodel import SQLModel


class FormaPagoRead(SQLModel):
    id: int
    codigo: str
    nombre: str
    activa: bool


class EstadoPedidoRead(SQLModel):
    id: int
    codigo: str
    nombre: str
    orden: int
