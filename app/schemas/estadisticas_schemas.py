from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class ResumenResponse(BaseModel):
    ventas_hoy: str
    ticket_promedio: str
    pedidos_activos: int
    ingresos_mes: str


class VentasPeriodoItem(BaseModel):
    periodo: str
    total_ventas: str
    cantidad_pedidos: int


class ProductoTopItem(BaseModel):
    producto_nombre: str
    ingresos: str
    cantidad_vendida: int


class PedidosEstadoItem(BaseModel):
    estado_codigo: str
    cantidad: int


class IngresoFormaPagoItem(BaseModel):
    forma_pago_codigo: str
    total: str
    cantidad: int
