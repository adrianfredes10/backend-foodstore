# codigos string que van a la tabla


class RolCodigo:
    ADMIN = "ADMIN"
    STOCK = "STOCK"
    PEDIDOS = "PEDIDOS"
    CLIENT = "CLIENT"


# FSM v7: 5 estados, sin EN_CAMINO
class EstadoPedidoCodigo:
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREP = "EN_PREP"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"
