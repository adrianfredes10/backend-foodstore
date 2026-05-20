# pedidos: estados snapshot historial stock
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status

from app.constants.codigos import EstadoPedidoCodigo, RolCodigo
from app.models.pedido import DetallePedido, HistorialEstadoPedido, Pedido
from app.schemas.catalogo_schemas import EstadoPedidoRead, FormaPagoRead
from app.schemas.direccion_schemas import DireccionRead
from app.schemas.pedido_schemas import (
    CambiarEstadoRequest,
    DetallePedidoRead,
    HistorialEstadoRead,
    ItemPedidoIn,
    PedidoCreate,
    PedidoRead,
)
from app.uow import UnitOfWork

# mapa de transiciones válidas por estado actual
TRANSICIONES: dict[str, list[str]] = {
    EstadoPedidoCodigo.PENDIENTE: [
        EstadoPedidoCodigo.CONFIRMADO,
        EstadoPedidoCodigo.CANCELADO,
    ],
    EstadoPedidoCodigo.CONFIRMADO: [
        EstadoPedidoCodigo.EN_PREP,
        EstadoPedidoCodigo.CANCELADO,
    ],
    EstadoPedidoCodigo.EN_PREP: [EstadoPedidoCodigo.EN_CAMINO],
    EstadoPedidoCodigo.EN_CAMINO: [EstadoPedidoCodigo.ENTREGADO],
    EstadoPedidoCodigo.ENTREGADO: [],
    EstadoPedidoCodigo.CANCELADO: [],
}


def _build_estado_read(e) -> EstadoPedidoRead:
    return EstadoPedidoRead(
        id=e.id, codigo=e.codigo, nombre=e.nombre, orden=e.orden
    )


class PedidoService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _armar_read(self, pedido: Pedido) -> PedidoRead:
        p = self.uow.pedidos.get_pedido(pedido.id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")

        estado = self.uow.pedidos.get_estado_by_id(p.estado_id)
        forma_pago = self.uow.pedidos.get_forma_pago(p.forma_pago_id)
        direccion = self.uow.direcciones.get_by_id_para_pedido(p.direccion_entrega_id)

        estado_read = _build_estado_read(estado)
        forma_read = FormaPagoRead(
            id=forma_pago.id,
            codigo=forma_pago.codigo,
            nombre=forma_pago.nombre,
            activa=forma_pago.activa,
        )
        dir_read = DireccionRead(
            id=direccion.id,
            usuario_id=direccion.usuario_id,
            alias=direccion.alias,
            calle=direccion.calle,
            numero=direccion.numero,
            referencia=direccion.referencia,
            ciudad=direccion.ciudad,
            codigo_postal=direccion.codigo_postal,
            es_principal=direccion.es_principal,
            created_at=direccion.created_at,
        )

        items_rd = [
            DetallePedidoRead(
                producto_id=d.producto_id,
                producto_nombre=d.producto_nombre,
                precio_unitario=d.precio_unitario,
                cantidad=d.cantidad,
                subtotal=d.subtotal,
            )
            for d in (p.detalles or [])
        ]

        hist_rd: List[HistorialEstadoRead] = []
        for h in sorted(p.historial or [], key=lambda x: x.fecha):
            est_ant = None
            if h.estado_anterior_id:
                e = self.uow.pedidos.get_estado_by_id(h.estado_anterior_id)
                if e:
                    est_ant = _build_estado_read(e)
            e_new = self.uow.pedidos.get_estado_by_id(h.estado_nuevo_id)
            hist_rd.append(
                HistorialEstadoRead(
                    estado_anterior=est_ant,
                    estado_nuevo=_build_estado_read(e_new),
                    usuario_id=h.usuario_id,
                    fecha=h.fecha,
                    observacion=h.observacion,
                )
            )

        return PedidoRead(
            id=p.id,
            usuario_id=p.usuario_id,
            direccion_entrega=dir_read,
            forma_pago=forma_read,
            estado=estado_read,
            total=p.total,
            observaciones=p.observaciones,
            fecha_creacion=p.created_at,
            fecha_confirmacion=p.fecha_confirmacion,
            fecha_entrega=p.fecha_entrega,
            items=items_rd,
            historial=hist_rd,
        )

    def crear(self, usuario_id: int, data: PedidoCreate) -> PedidoRead:
        with self.uow as uow:
            dire = uow.direcciones.get_owned(data.direccion_entrega_id, usuario_id)
            if not dire:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail="Dirección no encontrada o no es tuya",
                )
            fp = uow.pedidos.get_forma_pago(data.forma_pago_id)
            if not fp or not fp.activa:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, detail="Forma de pago inválida"
                )
            est_pend = uow.pedidos.get_estado_by_codigo(EstadoPedidoCodigo.PENDIENTE)
            if not est_pend:
                raise HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Falta estado PENDIENTE en BD (seed)",
                )

            total = Decimal("0")
            items_prep: list[tuple] = []

            for item in data.items:
                prod = uow.productos.get_by_id(item.producto_id)
                if not prod:
                    raise HTTPException(
                        status.HTTP_404_NOT_FOUND,
                        detail=f"Producto {item.producto_id} no existe",
                    )
                if not prod.disponible:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        detail=f"Producto '{prod.nombre}' no disponible",
                    )
                if prod.stock_cantidad < item.cantidad:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        detail=f"Stock insuficiente para '{prod.nombre}'",
                    )
                subtotal = prod.precio * Decimal(str(item.cantidad))
                total += subtotal
                items_prep.append((prod, item, subtotal))

            ped = Pedido(
                usuario_id=usuario_id,
                direccion_entrega_id=data.direccion_entrega_id,
                forma_pago_id=data.forma_pago_id,
                estado_id=est_pend.id,
                total=total,
                observaciones=data.observaciones,
            )
            uow.pedidos.create_pedido(ped)

            for prod, item, subtotal in items_prep:
                det = DetallePedido(
                    pedido_id=ped.id,
                    producto_id=prod.id,
                    producto_nombre=prod.nombre,
                    precio_unitario=prod.precio,
                    cantidad=item.cantidad,
                    subtotal=subtotal,
                )
                uow.pedidos.add_detalle(det)
                prod.stock_cantidad -= item.cantidad
                uow.session.add(prod)

            uow.pedidos.append_historial(
                HistorialEstadoPedido(
                    pedido_id=ped.id,
                    estado_anterior_id=None,
                    estado_nuevo_id=est_pend.id,
                    usuario_id=usuario_id,
                )
            )
            uow.flush()
            return self._armar_read(ped)

    def listar(
        self,
        *,
        usuario_id: Optional[int] = None,
        es_staff: bool,
        page: int = 1,
        size: int = 20,
        estado_codigo: Optional[str] = None,
        filtro_usuario_id: Optional[int] = None,
    ) -> List[PedidoRead]:
        skip = (page - 1) * size
        with self.uow as uow:
            if es_staff:
                items = uow.pedidos.list_all(
                    skip,
                    size,
                    estado_codigo=estado_codigo,
                    usuario_id=filtro_usuario_id,
                )
            else:
                if usuario_id is None:
                    return []
                items = uow.pedidos.list_for_usuario(
                    usuario_id, skip, size, estado_codigo=estado_codigo
                )
            return [self._armar_read(ped) for ped in items]

    def obtener(self, pedido_id: int, usuario_id: int, roles: set[str]) -> PedidoRead:
        with self.uow as uow:
            p = uow.pedidos.get_pedido(pedido_id)
            if not p:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
            if RolCodigo.ADMIN in roles or RolCodigo.PEDIDOS in roles:
                pass
            elif p.usuario_id != usuario_id:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, "No podés ver este pedido"
                )
            return self._armar_read(p)

    def cambiar_estado(
        self,
        pedido_id: int,
        nuevo_codigo: str,
        actor_id: int,
        roles: set[str],
        observacion: Optional[str] = None,
    ) -> PedidoRead:
        with self.uow as uow:
            p = uow.pedidos.get_pedido(pedido_id)
            if not p:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")

            estado_actual = uow.pedidos.get_estado_by_id(p.estado_id)
            cod_actual = estado_actual.codigo
            permitidos = TRANSICIONES.get(cod_actual, [])

            if nuevo_codigo not in permitidos:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Transición inválida: {cod_actual} → {nuevo_codigo}. "
                        f"Permitidas: {permitidos}"
                    ),
                )

            # cliente solo puede cancelar su propio pedido
            if RolCodigo.ADMIN not in roles and RolCodigo.PEDIDOS not in roles:
                if actor_id != p.usuario_id:
                    raise HTTPException(
                        status.HTTP_403_FORBIDDEN, "No podés modificar este pedido"
                    )
                if nuevo_codigo != EstadoPedidoCodigo.CANCELADO:
                    raise HTTPException(
                        status.HTTP_403_FORBIDDEN, "Solo podés cancelar tu propio pedido"
                    )

            est_nuevo = uow.pedidos.get_estado_by_codigo(nuevo_codigo)
            if not est_nuevo:
                raise HTTPException(500, detail=f"Falta estado {nuevo_codigo} (seed)")

            # devolver stock si se cancela
            if nuevo_codigo == EstadoPedidoCodigo.CANCELADO:
                for d in p.detalles or []:
                    if d.producto_id:
                        prod = uow.productos.get_by_id(d.producto_id)
                        if prod:
                            prod.stock_cantidad += d.cantidad
                            uow.session.add(prod)

            prev_id = p.estado_id
            uow.pedidos.set_estado(p, est_nuevo.id)

            if nuevo_codigo == EstadoPedidoCodigo.CONFIRMADO:
                p.fecha_confirmacion = datetime.now(timezone.utc)
                uow.session.add(p)
            if nuevo_codigo == EstadoPedidoCodigo.ENTREGADO:
                p.fecha_entrega = datetime.now(timezone.utc)
                uow.session.add(p)

            uow.pedidos.append_historial(
                HistorialEstadoPedido(
                    pedido_id=p.id,
                    estado_anterior_id=prev_id,
                    estado_nuevo_id=est_nuevo.id,
                    usuario_id=actor_id,
                    observacion=observacion,
                )
            )
            uow.flush()
            return self._armar_read(p)

    def avanzar_estado(self, pedido_id: int, actor_id: int) -> PedidoRead:
        with self.uow as uow:
            p = uow.pedidos.get_pedido(pedido_id)
            if not p:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
            estado_actual = uow.pedidos.get_estado_by_id(p.estado_id)
            cod_actual = estado_actual.codigo
            # toma el primer estado permitido que no sea CANCELADO
            siguientes = [
                c
                for c in TRANSICIONES.get(cod_actual, [])
                if c != EstadoPedidoCodigo.CANCELADO
            ]
            if not siguientes:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail="No hay transición siguiente desde este estado",
                )
            siguiente_codigo = siguientes[0]
        return self.cambiar_estado(
            pedido_id,
            siguiente_codigo,
            actor_id,
            {RolCodigo.ADMIN},
        )

    def cancelar(self, pedido_id: int, usuario_id: int) -> PedidoRead:
        return self.cambiar_estado(
            pedido_id,
            EstadoPedidoCodigo.CANCELADO,
            usuario_id,
            set(),
        )

    def obtener_historial(
        self, pedido_id: int, usuario_id: int, roles: set[str]
    ) -> List[HistorialEstadoRead]:
        with self.uow as uow:
            p = uow.pedidos.get_pedido(pedido_id)
            if not p:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
            if RolCodigo.ADMIN not in roles and RolCodigo.PEDIDOS not in roles:
                if p.usuario_id != usuario_id:
                    raise HTTPException(
                        status.HTTP_403_FORBIDDEN, "No podés ver este pedido"
                    )
            hist_rd: List[HistorialEstadoRead] = []
            for h in sorted(p.historial or [], key=lambda x: x.fecha):
                est_ant = None
                if h.estado_anterior_id:
                    e = uow.pedidos.get_estado_by_id(h.estado_anterior_id)
                    if e:
                        est_ant = _build_estado_read(e)
                e_new = uow.pedidos.get_estado_by_id(h.estado_nuevo_id)
                hist_rd.append(
                    HistorialEstadoRead(
                        estado_anterior=est_ant,
                        estado_nuevo=_build_estado_read(e_new),
                        usuario_id=h.usuario_id,
                        fecha=h.fecha,
                        observacion=h.observacion,
                    )
                )
            return hist_rd
