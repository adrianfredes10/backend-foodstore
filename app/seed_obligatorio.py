# datos minimos al startup: roles estados formas de pago y admin
# seed.py importa lo mismo cuando lo corres vos
import os

from sqlmodel import Session, select

from app.constants.codigos import EstadoPedidoCodigo, RolCodigo
from app.core.security import hash_password
from app.database import engine
from app.models.pedido import EstadoPedido, FormaPago
from app.models.seguridad import Rol, Usuario, UsuarioRol

ROLES_DATA = [
    (RolCodigo.ADMIN, "Administrador"),
    (RolCodigo.STOCK, "Gestor de stock"),
    (RolCodigo.PEDIDOS, "Gestor de pedidos"),
    (RolCodigo.CLIENT, "Cliente"),
]

# (codigo, nombre, orden)
ESTADOS_DATA = [
    (EstadoPedidoCodigo.PENDIENTE, "Pendiente", 1),
    (EstadoPedidoCodigo.CONFIRMADO, "Confirmado", 2),
    (EstadoPedidoCodigo.EN_PREP, "En preparacion", 3),
    (EstadoPedidoCodigo.EN_CAMINO, "En camino", 4),
    (EstadoPedidoCodigo.ENTREGADO, "Entregado", 5),
    (EstadoPedidoCodigo.CANCELADO, "Cancelado", 6),
]

FORMAS_DATA = [
    ("EFECTIVO", "Efectivo"),
    ("TARJETA", "Tarjeta debito/credito"),
    ("TRANSFERENCIA", "Transferencia bancaria"),
    ("MERCADOPAGO", "Mercado Pago"),
]


def seed_roles(session: Session) -> None:
    for codigo, nombre in ROLES_DATA:
        existing = session.exec(select(Rol).where(Rol.codigo == codigo)).first()
        if existing:
            continue
        session.add(Rol(codigo=codigo, nombre=nombre))
        session.flush()


def seed_estados_pedido(session: Session) -> None:
    for codigo, nombre, orden in ESTADOS_DATA:
        existing = session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == codigo)
        ).first()
        if existing:
            # actualizar orden si ya existe con valor 0
            if existing.orden == 0:
                existing.orden = orden
                session.add(existing)
            continue
        session.add(EstadoPedido(codigo=codigo, nombre=nombre, orden=orden))
        session.flush()


def seed_formas_pago(session: Session) -> None:
    for codigo, nombre in FORMAS_DATA:
        existing = session.exec(select(FormaPago).where(FormaPago.codigo == codigo)).first()
        if existing:
            continue
        session.add(FormaPago(codigo=codigo, nombre=nombre, activa=True))
        session.flush()


def seed_usuario_admin(session: Session) -> None:
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@foodstore.local")
    password = os.getenv("SEED_ADMIN_PASSWORD", "Admin1234!")
    existing = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if existing:
        return
    rol_admin = session.exec(select(Rol).where(Rol.codigo == RolCodigo.ADMIN)).first()
    if not rol_admin:
        return
    user = Usuario(
        email=email,
        password_hash=hash_password(password),
        nombre="Admin",
        apellido="Sistema",
        activo=True,
    )
    session.add(user)
    session.flush()
    session.add(UsuarioRol(usuario_id=user.id, rol_id=rol_admin.id))


def run_seed_obligatorio() -> None:
    with Session(engine) as session:
        seed_roles(session)
        seed_estados_pedido(session)
        seed_formas_pago(session)
        seed_usuario_admin(session)
        session.commit()
