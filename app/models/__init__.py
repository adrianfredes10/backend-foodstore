# registra modelos para create_all
from app.models.categoria import Categoria
from app.models.direccion_entrega import DireccionEntrega
from app.models.ingrediente import Ingrediente, ProductoIngrediente
from app.models.pedido import (
    DetallePedido,
    EstadoPedido,
    FormaPago,
    HistorialEstadoPedido,
    Pedido,
)
from app.models.producto import Producto
from app.models.seguridad import Rol, Usuario, UsuarioRol

__all__ = [
    "Categoria",
    "Ingrediente",
    "ProductoIngrediente",
    "Producto",
    "Rol",
    "Usuario",
    "UsuarioRol",
    "EstadoPedido",
    "FormaPago",
    "Pedido",
    "DetallePedido",
    "HistorialEstadoPedido",
    "DireccionEntrega",
]
