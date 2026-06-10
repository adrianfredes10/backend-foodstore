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
    es_terminal: bool = False


class UnidadMedidaRead(SQLModel):
    id: int
    nombre: str
    simbolo: str
    tipo: str
