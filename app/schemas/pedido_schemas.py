from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlmodel import SQLModel, Field

from app.schemas.catalogo_schemas import EstadoPedidoRead, FormaPagoRead
from app.schemas.direccion_schemas import DireccionRead


class ItemPedidoIn(SQLModel):
    producto_id: int = Field(gt=0)
    cantidad: float = Field(gt=0)


class PedidoCreate(SQLModel):
    direccion_entrega_id: int = Field(gt=0)
    forma_pago_id: int = Field(gt=0)
    items: List[ItemPedidoIn] = Field(min_length=1)
    observaciones: Optional[str] = Field(default=None, max_length=500)


class DetallePedidoRead(SQLModel):
    producto_id: Optional[int]
    producto_nombre: str
    precio_unitario: Decimal
    cantidad: float
    subtotal: Decimal


class HistorialEstadoRead(SQLModel):
    estado_anterior: Optional[EstadoPedidoRead]
    estado_nuevo: EstadoPedidoRead
    usuario_id: Optional[int]
    fecha: datetime
    observacion: Optional[str]


class PedidoRead(SQLModel):
    id: int
    usuario_id: int
    direccion_entrega: DireccionRead
    forma_pago: FormaPagoRead
    estado: EstadoPedidoRead
    total: Decimal
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_confirmacion: Optional[datetime]
    fecha_entrega: Optional[datetime]
    items: List[DetallePedidoRead]
    historial: List[HistorialEstadoRead]


class CambiarEstadoRequest(SQLModel):
    estado_codigo: str
    observacion: Optional[str] = None
