# pago MercadoPago de un pedido (spec v7)
# idempotency_key UUID generado por el backend (ID-01), nunca por el frontend
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Pago(SQLModel, table=True):
    __tablename__ = "pago"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedido.id", index=True)
    idempotency_key: str = Field(unique=True, index=True, max_length=36)
    mp_payment_id: Optional[str] = Field(default=None, max_length=100)
    mp_preference_id: Optional[str] = Field(default=None, max_length=100)
    # estados de MP: pending | approved | rejected | cancelled | ...
    mp_status: str = Field(default="pending", max_length=50)
    mp_status_detail: Optional[str] = Field(default=None, max_length=100)
    # metodo de pago usado en MP (visa, master, account_money...) — spec v7 §3.3
    payment_method_id: Optional[str] = Field(default=None, max_length=50)
    # referencia externa que viaja a MP (str del pedido_id) — spec v7 §3.3
    external_reference: Optional[str] = Field(default=None, index=True, max_length=100)
    transaction_amount: Decimal = Field(
        default=0, max_digits=12, decimal_places=2, ge=0
    )
    currency_id: str = Field(default="ARS", max_length=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
