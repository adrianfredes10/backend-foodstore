# schemas de pagos MercadoPago (CONTRATO-API §PAGOS)
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PagoCreateRequest(SQLModel):
    pedido_id: int = Field(gt=0)


class PagoCrearResponse(SQLModel):
    pago_id: int
    preference_id: str
    # init_point: URL del checkout de MP, la tienda redirige ahi
    init_point: Optional[str] = None
    # public key de MP para inicializar el SDK en el frontend
    public_key: Optional[str] = None


class PagoConfirmRequest(SQLModel):
    pedido_id: int = Field(gt=0)
    # opcional: si no viene, el backend busca el ultimo mp_payment_id del pedido
    payment_id: Optional[int] = Field(default=None, gt=0)


class PagoEstadoResponse(SQLModel):
    # "pendiente" | "aprobado" | "rechazado" | None (sin pago registrado)
    estado: Optional[str] = None
    pedido_id: int


class PagoRead(SQLModel):
    # lectura para el panel admin (read-only); el idempotency_key NO se expone
    id: int
    pedido_id: int
    mp_payment_id: Optional[str] = None
    mp_preference_id: Optional[str] = None
    mp_status: str
    mp_status_detail: Optional[str] = None
    transaction_amount: str
    currency_id: str
    created_at: datetime
    updated_at: datetime
