# datos minimos al startup: roles estados formas de pago y admin
# seed.py importa lo mismo cuando lo corres vos
import os

from sqlmodel import Session, select

from app.constants.codigos import EstadoPedidoCodigo, RolCodigo
from app.core.security import hash_password
from app.database import engine
from app.models.pedido import EstadoPedido, FormaPago
from app.models.direccion_entrega import DireccionEntrega
from app.models.seguridad import Rol, Usuario, UsuarioRol
from app.models.unidad_medida import UnidadMedida

ROLES_DATA = [
    (RolCodigo.ADMIN, "Administrador"),
    (RolCodigo.STOCK, "Gestor de stock"),
    (RolCodigo.PEDIDOS, "Gestor de pedidos"),
    (RolCodigo.CLIENT, "Cliente"),
]

# (codigo, nombre, orden, es_terminal) -- FSM v7: 5 estados, sin EN_CAMINO
ESTADOS_DATA = [
    (EstadoPedidoCodigo.PENDIENTE, "Pendiente", 1, False),
    (EstadoPedidoCodigo.CONFIRMADO, "Confirmado", 2, False),
    (EstadoPedidoCodigo.EN_PREP, "En preparacion", 3, False),
    (EstadoPedidoCodigo.ENTREGADO, "Entregado", 4, True),
    (EstadoPedidoCodigo.CANCELADO, "Cancelado", 5, True),
]

FORMAS_DATA = [
    ("EFECTIVO", "Efectivo"),
    ("TARJETA", "Tarjeta debito/credito"),
    ("TRANSFERENCIA", "Transferencia bancaria"),
    ("MERCADOPAGO", "Mercado Pago"),
]

# (nombre, simbolo, tipo) -- entidad v7 obligatoria en seed (PDF 12.2)
UNIDADES_DATA = [
    ("kilogramo", "kg", "peso"),
    ("gramo", "g", "peso"),
    ("litro", "L", "volumen"),
    ("mililitro", "ml", "volumen"),
    ("unidad", "ud", "contable"),
    ("porciones", "porc", "contable"),
]


def seed_roles(session: Session) -> None:
    for codigo, nombre in ROLES_DATA:
        existing = session.exec(select(Rol).where(Rol.codigo == codigo)).first()
        if existing:
            print(f"  [skip] rol '{codigo}' ya existe")
            continue
        session.add(Rol(codigo=codigo, nombre=nombre))
        session.flush()
        print(f"  [OK]   rol '{codigo}' insertado")


def seed_estados_pedido(session: Session) -> None:
    for codigo, nombre, orden, es_terminal in ESTADOS_DATA:
        existing = session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == codigo)
        ).first()
        if existing:
            # realinear orden y es_terminal si la fila viene de una version vieja
            existing.orden = orden
            existing.es_terminal = es_terminal
            session.add(existing)
            print(f"  [OK]   estado '{codigo}' actualizado")
            continue
        session.add(
            EstadoPedido(
                codigo=codigo,
                nombre=nombre,
                orden=orden,
                es_terminal=es_terminal,
            )
        )
        session.flush()
        print(f"  [OK]   estado '{codigo}' insertado")


def seed_formas_pago(session: Session) -> None:
    for codigo, nombre in FORMAS_DATA:
        existing = session.exec(select(FormaPago).where(FormaPago.codigo == codigo)).first()
        if existing:
            print(f"  [skip] forma_pago '{codigo}' ya existe")
            continue
        session.add(FormaPago(codigo=codigo, nombre=nombre, activa=True))
        session.flush()
        print(f"  [OK]   forma_pago '{codigo}' insertada")


def seed_unidades_medida(session: Session) -> None:
    for nombre, simbolo, tipo in UNIDADES_DATA:
        existing = session.exec(
            select(UnidadMedida).where(UnidadMedida.simbolo == simbolo)
        ).first()
        if existing:
            print(f"  [skip] unidad '{simbolo}' ya existe")
            continue
        session.add(UnidadMedida(nombre=nombre, simbolo=simbolo, tipo=tipo))
        session.flush()
        print(f"  [OK]   unidad '{simbolo}' insertada")


def seed_usuario_admin(session: Session) -> None:
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@foodstore.com")
    password = os.getenv("SEED_ADMIN_PASSWORD", "Admin1234!")
    existing = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if existing:
        print(f"  [skip] admin '{email}' ya existe")
        return
    rol_admin = session.exec(select(Rol).where(Rol.codigo == RolCodigo.ADMIN)).first()
    if not rol_admin:
        print("  [ERR]  rol ADMIN no encontrado, saltando admin")
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
    print(f"  [OK]   admin '{email}' creado (id={user.id})")


def _seed_direccion_cliente(session: Session, usuario_id: int) -> None:
    existing = session.exec(
        select(DireccionEntrega).where(DireccionEntrega.usuario_id == usuario_id)
    ).first()
    if existing:
        print(f"  [skip] dirección para usuario {usuario_id} ya existe")
        return
    session.add(DireccionEntrega(
        usuario_id=usuario_id,
        alias="Casa",
        calle="Av. Siempreviva",
        numero="742",
        referencia="Timbre azul",
        ciudad="Buenos Aires",
        codigo_postal="1414",
        es_principal=True,
    ))
    session.flush()
    print(f"  [OK]   dirección principal creada para usuario {usuario_id}")


def seed_usuario_cliente(session: Session) -> None:
    email = os.getenv("SEED_CLIENT_EMAIL", "cliente@foodstore.local")
    password = os.getenv("SEED_CLIENT_PASSWORD", "Cliente1234!")
    existing = session.exec(select(Usuario).where(Usuario.email == email)).first()
    if existing:
        print(f"  [skip] cliente '{email}' ya existe")
        _seed_direccion_cliente(session, existing.id)
        return
    rol_client = session.exec(select(Rol).where(Rol.codigo == RolCodigo.CLIENT)).first()
    if not rol_client:
        print("  [ERR]  rol CLIENT no encontrado, saltando cliente")
        return
    user = Usuario(
        email=email,
        password_hash=hash_password(password),
        nombre="Cliente",
        apellido="FoodStore",
        activo=True,
    )
    session.add(user)
    session.flush()
    session.add(UsuarioRol(usuario_id=user.id, rol_id=rol_client.id))
    session.flush()
    print(f"  [OK]   cliente '{email}' creado (id={user.id})")
    _seed_direccion_cliente(session, user.id)


def run_seed_obligatorio() -> None:
    print("=== seed_obligatorio: inicio ===")
    with Session(engine) as session:
        print("--- roles ---")
        seed_roles(session)
        print("--- estados de pedido ---")
        seed_estados_pedido(session)
        print("--- formas de pago ---")
        seed_formas_pago(session)
        print("--- unidades de medida ---")
        seed_unidades_medida(session)
        print("--- usuario admin ---")
        seed_usuario_admin(session)
        print("--- usuario cliente ---")
        seed_usuario_cliente(session)
        session.commit()
    print("=== seed_obligatorio: commit OK ===")


if __name__ == "__main__":
    run_seed_obligatorio()
