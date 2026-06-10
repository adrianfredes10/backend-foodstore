# pedido detalle estados pago historial
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True, index=True, max_length=32)
    nombre: str = Field(max_length=120)
    orden: int = Field(default=0)
    # estado terminal: no admite transiciones salientes (RN-01)
    es_terminal: bool = Field(default=False)


class FormaPago(SQLModel, table=True):
    __tablename__ = "forma_pago"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(unique=True, index=True, max_length=32)
    nombre: str = Field(max_length=120)
    activa: bool = Field(default=True)


class Pedido(SQLModel, table=True):
    __tablename__ = "pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    direccion_entrega_id: int = Field(foreign_key="direccion_entrega.id")
    forma_pago_id: int = Field(foreign_key="forma_pago.id")
    estado_id: int = Field(foreign_key="estado_pedido.id", index=True)
    # montos v7: total = subtotal - descuento + costo_envio
    subtotal: Decimal = Field(default=0, max_digits=12, decimal_places=2, ge=0)
    descuento: Decimal = Field(default=0, max_digits=12, decimal_places=2, ge=0)
    costo_envio: Decimal = Field(default=0, max_digits=12, decimal_places=2, ge=0)
    total: Decimal = Field(max_digits=12, decimal_places=2, ge=0)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    fecha_confirmacion: Optional[datetime] = Field(default=None)
    fecha_entrega: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    detalles: List["DetallePedido"] = Relationship(back_populates="pedido")
    historial: List["HistorialEstadoPedido"] = Relationship(back_populates="pedido")


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", index=True)
    producto_id: Optional[int] = Field(default=None, foreign_key="producto.id")
    # snapshot: copia del nombre y precio al momento de crear el pedido
    producto_nombre: str = Field(max_length=200)
    precio_unitario: Decimal = Field(max_digits=12, decimal_places=2, ge=0)
    cantidad: float = Field(gt=0)
    subtotal: Decimal = Field(max_digits=12, decimal_places=2, ge=0)

    pedido: Optional[Pedido] = Relationship(back_populates="detalles")


class HistorialEstadoPedido(SQLModel, table=True):
    # solo inserts, nunca update ni delete (audit trail)
    __tablename__ = "historial_estado_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", index=True)
    estado_anterior_id: Optional[int] = Field(
        default=None,
        foreign_key="estado_pedido.id",
    )
    estado_nuevo_id: int = Field(foreign_key="estado_pedido.id")
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    fecha: datetime = Field(default_factory=datetime.utcnow)
    observacion: Optional[str] = Field(default=None, max_length=500)

    pedido: Optional[Pedido] = Relationship(back_populates="historial")
