"""
script de seeding inserta datos de prueba
correr manual:
  python seed.py           -> idempotente, agrega lo que falta
  python seed.py --reset   -> limpia pedidos/productos/ingredientes/categorias y re-seedea todo
"""
import sys
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from sqlmodel import Session, delete, select

from app.constants.codigos import EstadoPedidoCodigo, RolCodigo
from app.core.security import hash_password
from app.database import create_db_and_tables, engine
from app.models.categoria import Categoria
from app.models.direccion_entrega import DireccionEntrega
from app.models.ingrediente import Ingrediente, ProductoIngrediente
from app.models.pedido import DetallePedido, EstadoPedido, FormaPago, HistorialEstadoPedido, Pedido
from app.models.producto import Producto
from app.models.seguridad import Rol, Usuario, UsuarioRol
from app.seed_obligatorio import (
    seed_estados_pedido,
    seed_formas_pago,
    seed_roles,
    seed_usuario_admin,
)

CATEGORIAS = [
    {"nombre": "Bebidas Calientes",   "descripcion": "Cafés, tés e infusiones"},
    {"nombre": "Bebidas Frías",       "descripcion": "Jugos, licuados y frapés"},
    {"nombre": "Desayunos",           "descripcion": "Opciones para empezar el día"},
    {"nombre": "Sándwiches y Wraps",  "descripcion": "Sándwiches, wraps y tostados"},
    {"nombre": "Pizzas",              "descripcion": "Pizzas artesanales al horno"},
    {"nombre": "Pastas",              "descripcion": "Pastas frescas y secas"},
    {"nombre": "Ensaladas",           "descripcion": "Ensaladas frescas y completas"},
    {"nombre": "Entradas",            "descripcion": "Entradas y snacks"},
    {"nombre": "Comidas",             "descripcion": "Platos principales"},
    {"nombre": "Postres",             "descripcion": "Dulces, tortas y helados"},
]

INGREDIENTES = [
    {"nombre": "Leche",            "unidad_medida": "ml",       "stock_actual": 20000, "stock_minimo": 3000},
    {"nombre": "Café",             "unidad_medida": "g",        "stock_actual": 5000,  "stock_minimo": 800},
    {"nombre": "Azúcar",           "unidad_medida": "g",        "stock_actual": 8000,  "stock_minimo": 1500},
    {"nombre": "Harina",           "unidad_medida": "g",        "stock_actual": 12000, "stock_minimo": 2000},
    {"nombre": "Huevo",            "unidad_medida": "unidades", "stock_actual": 120,   "stock_minimo": 24},
    {"nombre": "Manteca",          "unidad_medida": "g",        "stock_actual": 4000,  "stock_minimo": 600},
    {"nombre": "Cacao",            "unidad_medida": "g",        "stock_actual": 2000,  "stock_minimo": 400},
    {"nombre": "Crema",            "unidad_medida": "ml",       "stock_actual": 5000,  "stock_minimo": 800},
    {"nombre": "Frutillas",        "unidad_medida": "g",        "stock_actual": 4000,  "stock_minimo": 600},
    {"nombre": "Jugo de naranja",  "unidad_medida": "ml",       "stock_actual": 6000,  "stock_minimo": 1200},
    {"nombre": "Queso mozzarella", "unidad_medida": "g",        "stock_actual": 6000,  "stock_minimo": 1000},
    {"nombre": "Jamón cocido",     "unidad_medida": "g",        "stock_actual": 3000,  "stock_minimo": 600},
    {"nombre": "Pan de molde",     "unidad_medida": "unidades", "stock_actual": 100,   "stock_minimo": 20},
    {"nombre": "Pan de sándwich",  "unidad_medida": "unidades", "stock_actual": 80,    "stock_minimo": 16},
    {"nombre": "Tomate",           "unidad_medida": "g",        "stock_actual": 5000,  "stock_minimo": 800},
    {"nombre": "Lechuga",          "unidad_medida": "g",        "stock_actual": 3000,  "stock_minimo": 500},
    {"nombre": "Pollo",            "unidad_medida": "g",        "stock_actual": 8000,  "stock_minimo": 1500},
    {"nombre": "Carne molida",     "unidad_medida": "g",        "stock_actual": 7000,  "stock_minimo": 1200},
    {"nombre": "Pasta seca",       "unidad_medida": "g",        "stock_actual": 6000,  "stock_minimo": 1000},
    {"nombre": "Salsa de tomate",  "unidad_medida": "ml",       "stock_actual": 8000,  "stock_minimo": 1200},
    {"nombre": "Aceite de oliva",  "unidad_medida": "ml",       "stock_actual": 3000,  "stock_minimo": 400},
    {"nombre": "Ajo",              "unidad_medida": "g",        "stock_actual": 500,   "stock_minimo": 100},
    {"nombre": "Cebolla",          "unidad_medida": "g",        "stock_actual": 4000,  "stock_minimo": 600},
    {"nombre": "Papa",             "unidad_medida": "g",        "stock_actual": 10000, "stock_minimo": 1500},
    {"nombre": "Limón",            "unidad_medida": "unidades", "stock_actual": 60,    "stock_minimo": 12},
    {"nombre": "Banana",           "unidad_medida": "unidades", "stock_actual": 50,    "stock_minimo": 10},
    {"nombre": "Mango",            "unidad_medida": "g",        "stock_actual": 4000,  "stock_minimo": 600},
    {"nombre": "Chocolate amargo", "unidad_medida": "g",        "stock_actual": 2500,  "stock_minimo": 400},
    {"nombre": "Queso crema",      "unidad_medida": "g",        "stock_actual": 2500,  "stock_minimo": 400},
    {"nombre": "Orégano",          "unidad_medida": "g",        "stock_actual": 400,   "stock_minimo": 50},
]

PRODUCTOS = [
    # === Bebidas Calientes ===
    {
        "nombre": "Cappuccino",
        "descripcion": "Café espresso con leche espumosa",
        "precio": 450.00,
        "disponible": True,
        "categoria": "Bebidas Calientes",
        "ingredientes": [
            {"nombre": "Leche", "cantidad": 200},
            {"nombre": "Café",  "cantidad": 30},
        ],
    },
    {
        "nombre": "Café con Leche",
        "descripcion": "Café suave con leche caliente",
        "precio": 350.00,
        "disponible": True,
        "categoria": "Bebidas Calientes",
        "ingredientes": [
            {"nombre": "Leche",  "cantidad": 250},
            {"nombre": "Café",   "cantidad": 20},
            {"nombre": "Azúcar", "cantidad": 10},
        ],
    },
    {
        "nombre": "Latte",
        "descripcion": "Espresso con abundante leche vaporizada",
        "precio": 480.00,
        "disponible": True,
        "categoria": "Bebidas Calientes",
        "ingredientes": [
            {"nombre": "Leche", "cantidad": 300},
            {"nombre": "Café",  "cantidad": 25},
        ],
    },
    {
        "nombre": "Espresso Doble",
        "descripcion": "Doble ristretto concentrado",
        "precio": 300.00,
        "disponible": True,
        "categoria": "Bebidas Calientes",
        "ingredientes": [
            {"nombre": "Café", "cantidad": 60},
        ],
    },
    {
        "nombre": "Té Verde",
        "descripcion": "Té verde con miel y limón",
        "precio": 280.00,
        "disponible": True,
        "categoria": "Bebidas Calientes",
        "ingredientes": [
            {"nombre": "Limón",  "cantidad": 0.5},
            {"nombre": "Azúcar", "cantidad": 10},
        ],
    },
    # === Bebidas Frías ===
    {
        "nombre": "Licuado de Frutilla",
        "descripcion": "Licuado fresco de frutillas con leche",
        "precio": 500.00,
        "disponible": True,
        "categoria": "Bebidas Frías",
        "ingredientes": [
            {"nombre": "Leche",     "cantidad": 300},
            {"nombre": "Frutillas", "cantidad": 150},
            {"nombre": "Azúcar",    "cantidad": 20},
        ],
    },
    {
        "nombre": "Jugo de Naranja",
        "descripcion": "Jugo natural exprimido",
        "precio": 380.00,
        "disponible": True,
        "categoria": "Bebidas Frías",
        "ingredientes": [
            {"nombre": "Jugo de naranja", "cantidad": 300},
        ],
    },
    {
        "nombre": "Smoothie de Mango",
        "descripcion": "Smoothie tropical de mango con leche",
        "precio": 550.00,
        "disponible": True,
        "categoria": "Bebidas Frías",
        "ingredientes": [
            {"nombre": "Mango",  "cantidad": 200},
            {"nombre": "Leche",  "cantidad": 150},
            {"nombre": "Azúcar", "cantidad": 15},
        ],
    },
    {
        "nombre": "Limonada Natural",
        "descripcion": "Limonada artesanal con menta",
        "precio": 320.00,
        "disponible": True,
        "categoria": "Bebidas Frías",
        "ingredientes": [
            {"nombre": "Limón",  "cantidad": 2},
            {"nombre": "Azúcar", "cantidad": 30},
        ],
    },
    {
        "nombre": "Licuado de Banana",
        "descripcion": "Licuado cremoso de banana con leche",
        "precio": 450.00,
        "disponible": True,
        "categoria": "Bebidas Frías",
        "ingredientes": [
            {"nombre": "Banana", "cantidad": 2},
            {"nombre": "Leche",  "cantidad": 250},
            {"nombre": "Azúcar", "cantidad": 10},
        ],
    },
    # === Desayunos ===
    {
        "nombre": "Medialunas",
        "descripcion": "3 medialunas de manteca artesanales",
        "precio": 400.00,
        "disponible": True,
        "categoria": "Desayunos",
        "ingredientes": [
            {"nombre": "Harina",  "cantidad": 200},
            {"nombre": "Manteca", "cantidad": 80},
            {"nombre": "Azúcar",  "cantidad": 30},
            {"nombre": "Huevo",   "cantidad": 2},
        ],
    },
    {
        "nombre": "Tostado de Jamón y Queso",
        "descripcion": "Tostado caliente con jamón y queso mozzarella",
        "precio": 550.00,
        "disponible": True,
        "categoria": "Desayunos",
        "ingredientes": [
            {"nombre": "Pan de molde",     "cantidad": 2},
            {"nombre": "Jamón cocido",     "cantidad": 60},
            {"nombre": "Queso mozzarella", "cantidad": 50},
            {"nombre": "Manteca",          "cantidad": 10},
        ],
    },
    {
        "nombre": "Croissant de Manteca",
        "descripcion": "Croissant hojaldrado de manteca",
        "precio": 350.00,
        "disponible": True,
        "categoria": "Desayunos",
        "ingredientes": [
            {"nombre": "Harina",  "cantidad": 150},
            {"nombre": "Manteca", "cantidad": 100},
            {"nombre": "Azúcar",  "cantidad": 20},
            {"nombre": "Huevo",   "cantidad": 1},
        ],
    },
    # === Sándwiches y Wraps ===
    {
        "nombre": "Sándwich de Pollo",
        "descripcion": "Sándwich con pollo grillado, lechuga y tomate",
        "precio": 750.00,
        "disponible": True,
        "categoria": "Sándwiches y Wraps",
        "ingredientes": [
            {"nombre": "Pan de sándwich", "cantidad": 2},
            {"nombre": "Pollo",           "cantidad": 150},
            {"nombre": "Lechuga",         "cantidad": 30},
            {"nombre": "Tomate",          "cantidad": 50},
        ],
    },
    {
        "nombre": "Sándwich Caprese",
        "descripcion": "Tomate, mozzarella y aceite de oliva en pan artesanal",
        "precio": 650.00,
        "disponible": True,
        "categoria": "Sándwiches y Wraps",
        "ingredientes": [
            {"nombre": "Pan de sándwich",  "cantidad": 2},
            {"nombre": "Tomate",           "cantidad": 80},
            {"nombre": "Queso mozzarella", "cantidad": 80},
            {"nombre": "Aceite de oliva",  "cantidad": 15},
        ],
    },
    # === Pizzas ===
    {
        "nombre": "Pizza Margherita",
        "descripcion": "Salsa de tomate, mozzarella y orégano",
        "precio": 1200.00,
        "disponible": True,
        "categoria": "Pizzas",
        "ingredientes": [
            {"nombre": "Harina",           "cantidad": 300},
            {"nombre": "Salsa de tomate",  "cantidad": 150},
            {"nombre": "Queso mozzarella", "cantidad": 200},
            {"nombre": "Orégano",          "cantidad": 5},
            {"nombre": "Aceite de oliva",  "cantidad": 20},
        ],
    },
    {
        "nombre": "Pizza Napolitana",
        "descripcion": "Margherita con tomate fresco y ajo",
        "precio": 1350.00,
        "disponible": True,
        "categoria": "Pizzas",
        "ingredientes": [
            {"nombre": "Harina",           "cantidad": 300},
            {"nombre": "Salsa de tomate",  "cantidad": 150},
            {"nombre": "Queso mozzarella", "cantidad": 200},
            {"nombre": "Tomate",           "cantidad": 100},
            {"nombre": "Ajo",              "cantidad": 10},
            {"nombre": "Orégano",          "cantidad": 5},
        ],
    },
    {
        "nombre": "Pizza de Jamón y Queso",
        "descripcion": "Pizza clásica con jamón cocido y doble mozzarella",
        "precio": 1280.00,
        "disponible": True,
        "categoria": "Pizzas",
        "ingredientes": [
            {"nombre": "Harina",           "cantidad": 300},
            {"nombre": "Salsa de tomate",  "cantidad": 150},
            {"nombre": "Queso mozzarella", "cantidad": 250},
            {"nombre": "Jamón cocido",     "cantidad": 120},
        ],
    },
    # === Pastas ===
    {
        "nombre": "Pasta Bolognesa",
        "descripcion": "Pasta con salsa de carne y tomate",
        "precio": 950.00,
        "disponible": True,
        "categoria": "Pastas",
        "ingredientes": [
            {"nombre": "Pasta seca",      "cantidad": 150},
            {"nombre": "Carne molida",    "cantidad": 120},
            {"nombre": "Salsa de tomate", "cantidad": 150},
            {"nombre": "Cebolla",         "cantidad": 50},
            {"nombre": "Ajo",             "cantidad": 5},
        ],
    },
    {
        "nombre": "Pasta Primavera",
        "descripcion": "Pasta con vegetales salteados y aceite de oliva",
        "precio": 850.00,
        "disponible": True,
        "categoria": "Pastas",
        "ingredientes": [
            {"nombre": "Pasta seca",     "cantidad": 150},
            {"nombre": "Tomate",         "cantidad": 80},
            {"nombre": "Cebolla",        "cantidad": 40},
            {"nombre": "Aceite de oliva","cantidad": 30},
            {"nombre": "Ajo",            "cantidad": 5},
        ],
    },
    # === Ensaladas ===
    {
        "nombre": "Ensalada César",
        "descripcion": "Lechuga romana, pollo grillado y aderezo césar",
        "precio": 780.00,
        "disponible": True,
        "categoria": "Ensaladas",
        "ingredientes": [
            {"nombre": "Lechuga",          "cantidad": 150},
            {"nombre": "Pollo",            "cantidad": 100},
            {"nombre": "Queso mozzarella", "cantidad": 40},
            {"nombre": "Aceite de oliva",  "cantidad": 20},
        ],
    },
    {
        "nombre": "Ensalada Mixta",
        "descripcion": "Lechuga, tomate, cebolla y aceite de oliva",
        "precio": 550.00,
        "disponible": True,
        "categoria": "Ensaladas",
        "ingredientes": [
            {"nombre": "Lechuga",        "cantidad": 100},
            {"nombre": "Tomate",         "cantidad": 80},
            {"nombre": "Cebolla",        "cantidad": 30},
            {"nombre": "Aceite de oliva","cantidad": 15},
        ],
    },
    # === Entradas ===
    {
        "nombre": "Empanadas de Carne x4",
        "descripcion": "4 empanadas de carne jugosas al horno",
        "precio": 700.00,
        "disponible": True,
        "categoria": "Entradas",
        "ingredientes": [
            {"nombre": "Harina",       "cantidad": 200},
            {"nombre": "Carne molida", "cantidad": 180},
            {"nombre": "Cebolla",      "cantidad": 60},
            {"nombre": "Huevo",        "cantidad": 2},
        ],
    },
    {
        "nombre": "Papas Fritas",
        "descripcion": "Papas fritas crocantes con sal",
        "precio": 450.00,
        "disponible": True,
        "categoria": "Entradas",
        "ingredientes": [
            {"nombre": "Papa",         "cantidad": 250},
            {"nombre": "Aceite de oliva","cantidad": 30},
        ],
    },
    # === Comidas ===
    {
        "nombre": "Milanesa de Pollo",
        "descripcion": "Milanesa de pechuga de pollo con papas fritas",
        "precio": 1100.00,
        "disponible": True,
        "categoria": "Comidas",
        "ingredientes": [
            {"nombre": "Pollo",  "cantidad": 200},
            {"nombre": "Huevo",  "cantidad": 1},
            {"nombre": "Harina", "cantidad": 80},
            {"nombre": "Papa",   "cantidad": 200},
        ],
    },
    {
        "nombre": "Hamburguesa Clásica",
        "descripcion": "Hamburguesa de carne con queso, lechuga y tomate",
        "precio": 1050.00,
        "disponible": True,
        "categoria": "Comidas",
        "ingredientes": [
            {"nombre": "Carne molida",     "cantidad": 180},
            {"nombre": "Pan de sándwich",  "cantidad": 2},
            {"nombre": "Queso mozzarella", "cantidad": 50},
            {"nombre": "Lechuga",          "cantidad": 20},
            {"nombre": "Tomate",           "cantidad": 40},
        ],
    },
    # === Postres ===
    {
        "nombre": "Torta de Chocolate",
        "descripcion": "Porción de torta húmeda de chocolate",
        "precio": 650.00,
        "disponible": True,
        "categoria": "Postres",
        "ingredientes": [
            {"nombre": "Harina",  "cantidad": 150},
            {"nombre": "Cacao",   "cantidad": 80},
            {"nombre": "Azúcar",  "cantidad": 100},
            {"nombre": "Huevo",   "cantidad": 3},
            {"nombre": "Manteca", "cantidad": 100},
            {"nombre": "Crema",   "cantidad": 100},
        ],
    },
    {
        "nombre": "Brownie de Chocolate",
        "descripcion": "Brownie húmedo con chocolate amargo",
        "precio": 520.00,
        "disponible": True,
        "categoria": "Postres",
        "ingredientes": [
            {"nombre": "Chocolate amargo", "cantidad": 100},
            {"nombre": "Manteca",          "cantidad": 80},
            {"nombre": "Azúcar",           "cantidad": 120},
            {"nombre": "Huevo",            "cantidad": 2},
            {"nombre": "Harina",           "cantidad": 60},
        ],
    },
    {
        "nombre": "Cheesecake de Frutilla",
        "descripcion": "Cheesecake cremoso con coulis de frutilla",
        "precio": 680.00,
        "disponible": True,
        "categoria": "Postres",
        "ingredientes": [
            {"nombre": "Queso crema", "cantidad": 200},
            {"nombre": "Crema",       "cantidad": 100},
            {"nombre": "Azúcar",      "cantidad": 80},
            {"nombre": "Frutillas",   "cantidad": 100},
            {"nombre": "Harina",      "cantidad": 50},
            {"nombre": "Manteca",     "cantidad": 40},
        ],
    },
]


def seed_categorias(session: Session) -> dict[str, Categoria]:
    resultado = {}
    for data in CATEGORIAS:
        existing = session.exec(
            select(Categoria).where(
                Categoria.nombre == data["nombre"],
                Categoria.deleted_at.is_(None),
            )
        ).first()
        if existing:
            resultado[data["nombre"]] = existing
        else:
            cat = Categoria(**data)
            session.add(cat)
            session.flush()
            resultado[data["nombre"]] = cat
    return resultado


def seed_ingredientes(session: Session) -> dict[str, Ingrediente]:
    resultado = {}
    for data in INGREDIENTES:
        existing = session.exec(
            select(Ingrediente).where(
                Ingrediente.nombre == data["nombre"],
                Ingrediente.deleted_at.is_(None),
            )
        ).first()
        if existing:
            resultado[data["nombre"]] = existing
        else:
            ing = Ingrediente(**data)
            session.add(ing)
            session.flush()
            resultado[data["nombre"]] = ing
    return resultado


def seed_productos(
    session: Session,
    categorias: dict[str, Categoria],
    ingredientes: dict[str, Ingrediente],
) -> None:
    for data in PRODUCTOS:
        existing = session.exec(
            select(Producto).where(
                Producto.nombre == data["nombre"],
                Producto.deleted_at.is_(None),
            )
        ).first()
        if existing:
            continue

        cat = categorias.get(data["categoria"])
        if not cat:
            continue

        producto = Producto(
            nombre=data["nombre"],
            descripcion=data["descripcion"],
            precio=data["precio"],
            disponible=data["disponible"],
            stock_cantidad=data.get("stock_cantidad", 100.0),
            categoria_id=cat.id,
        )
        session.add(producto)
        session.flush()

        for ing_data in data["ingredientes"]:
            ing = ingredientes.get(ing_data["nombre"])
            if not ing:
                continue
            session.add(
                ProductoIngrediente(
                    producto_id=producto.id,
                    ingrediente_id=ing.id,
                    cantidad=ing_data["cantidad"],
                    es_alergeno=ing_data.get("es_alergeno", False),
                )
            )


STAFF_DATA = [
    {"email": "stock@foodstore.local",   "password": "Stock1234!",   "nombre": "Gestor",  "apellido": "Stock",   "rol": RolCodigo.STOCK},
    {"email": "pedidos@foodstore.local", "password": "Pedidos1234!", "nombre": "Gestor",  "apellido": "Pedidos", "rol": RolCodigo.PEDIDOS},
]


def seed_usuarios_staff(session: Session) -> None:
    for data in STAFF_DATA:
        if session.exec(select(Usuario).where(Usuario.email == data["email"])).first():
            continue
        rol = session.exec(select(Rol).where(Rol.codigo == data["rol"])).first()
        if not rol:
            continue
        user = Usuario(
            email=data["email"],
            password_hash=hash_password(data["password"]),
            nombre=data["nombre"],
            apellido=data["apellido"],
            activo=True,
        )
        session.add(user)
        session.flush()
        session.add(UsuarioRol(usuario_id=user.id, rol_id=rol.id))
        session.flush()


CLIENTES_DATA = [
    {
        "email": "juan@cliente.com",
        "password": "Cliente123!",
        "nombre": "Juan",
        "apellido": "Pérez",
        "telefono": "1122334455",
        "direccion": {
            "alias": "Casa",
            "calle": "Av. Corrientes",
            "numero": "1234",
            "ciudad": "Buenos Aires",
            "codigo_postal": "1043",
            "es_principal": True,
        },
    },
]

PEDIDOS_DATA = [
    # === Juan ===
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "MERCADOPAGO",
        "estado_final": EstadoPedidoCodigo.ENTREGADO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP, EstadoPedidoCodigo.EN_CAMINO],
        "observaciones": "Sin azúcar por favor",
        "items": [("Cappuccino", 2), ("Medialunas", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "EFECTIVO",
        "estado_final": EstadoPedidoCodigo.PENDIENTE,
        "estados_intermedios": [],
        "observaciones": None,
        "items": [("Jugo de Naranja", 3)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TARJETA",
        "estado_final": EstadoPedidoCodigo.EN_PREP,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO],
        "observaciones": "Tocar timbre 3B",
        "items": [("Torta de Chocolate", 1), ("Café con Leche", 2), ("Licuado de Frutilla", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TRANSFERENCIA",
        "estado_final": EstadoPedidoCodigo.CANCELADO,
        "estados_intermedios": [],
        "observaciones": None,
        "items": [("Cappuccino", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "MERCADOPAGO",
        "estado_final": EstadoPedidoCodigo.CONFIRMADO,
        "estados_intermedios": [],
        "observaciones": "Extra queso en la pizza",
        "items": [("Pizza Margherita", 1), ("Empanadas de Carne x4", 1), ("Latte", 2)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TARJETA",
        "estado_final": EstadoPedidoCodigo.EN_CAMINO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP],
        "observaciones": None,
        "items": [("Pasta Bolognesa", 1), ("Ensalada César", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "EFECTIVO",
        "estado_final": EstadoPedidoCodigo.ENTREGADO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP, EstadoPedidoCodigo.EN_CAMINO],
        "observaciones": None,
        "items": [("Sándwich de Pollo", 2), ("Papas Fritas", 1), ("Limonada Natural", 2)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "MERCADOPAGO",
        "estado_final": EstadoPedidoCodigo.ENTREGADO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP, EstadoPedidoCodigo.EN_CAMINO],
        "observaciones": "Doble porción de papas",
        "items": [("Hamburguesa Clásica", 1), ("Papas Fritas", 2), ("Licuado de Banana", 1)],
    },
    # === María ===
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "MERCADOPAGO",
        "estado_final": EstadoPedidoCodigo.ENTREGADO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP, EstadoPedidoCodigo.EN_CAMINO],
        "observaciones": None,
        "items": [("Tostado de Jamón y Queso", 1), ("Café con Leche", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TARJETA",
        "estado_final": EstadoPedidoCodigo.CONFIRMADO,
        "estados_intermedios": [],
        "observaciones": "Sin cebolla",
        "items": [("Pizza Napolitana", 1), ("Latte", 2)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "EFECTIVO",
        "estado_final": EstadoPedidoCodigo.PENDIENTE,
        "estados_intermedios": [],
        "observaciones": None,
        "items": [("Cheesecake de Frutilla", 2), ("Brownie de Chocolate", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TARJETA",
        "estado_final": EstadoPedidoCodigo.EN_PREP,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO],
        "observaciones": "Aderezo aparte",
        "items": [("Ensalada Mixta", 1), ("Sándwich Caprese", 1), ("Limonada Natural", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "MERCADOPAGO",
        "estado_final": EstadoPedidoCodigo.ENTREGADO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP, EstadoPedidoCodigo.EN_CAMINO],
        "observaciones": None,
        "items": [("Empanadas de Carne x4", 2), ("Papas Fritas", 1), ("Espresso Doble", 2)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TRANSFERENCIA",
        "estado_final": EstadoPedidoCodigo.EN_CAMINO,
        "estados_intermedios": [EstadoPedidoCodigo.CONFIRMADO, EstadoPedidoCodigo.EN_PREP],
        "observaciones": None,
        "items": [("Pasta Primavera", 1), ("Ensalada Mixta", 1), ("Té Verde", 1)],
    },
    {
        "cliente_email": "juan@cliente.com",
        "forma_pago": "TARJETA",
        "estado_final": EstadoPedidoCodigo.CANCELADO,
        "estados_intermedios": [],
        "observaciones": None,
        "items": [("Milanesa de Pollo", 1)],
    },
]


def seed_pedidos(session: Session) -> None:
    rol_client = session.exec(select(Rol).where(Rol.codigo == RolCodigo.CLIENT)).first()
    if not rol_client:
        return

    # crear clientes y sus direcciones
    usuarios: dict[str, Usuario] = {}
    for data in CLIENTES_DATA:
        user = session.exec(select(Usuario).where(Usuario.email == data["email"])).first()
        if not user:
            user = Usuario(
                email=data["email"],
                password_hash=hash_password(data["password"]),
                nombre=data["nombre"],
                apellido=data["apellido"],
                telefono=data["telefono"],
                activo=True,
            )
            session.add(user)
            session.flush()
            session.add(UsuarioRol(usuario_id=user.id, rol_id=rol_client.id))

            direccion = DireccionEntrega(usuario_id=user.id, **data["direccion"])
            session.add(direccion)
            session.flush()

        usuarios[data["email"]] = user

    # mapas de lookup
    formas_pago: dict[str, FormaPago] = {
        fp.codigo: fp for fp in session.exec(select(FormaPago)).all()
    }
    estados: dict[str, EstadoPedido] = {
        ep.codigo: ep for ep in session.exec(select(EstadoPedido)).all()
    }

    if session.exec(select(Pedido)).first():
        return

    for pedido_data in PEDIDOS_DATA:
        user = usuarios.get(pedido_data["cliente_email"])
        if not user:
            continue

        direccion = session.exec(
            select(DireccionEntrega).where(DireccionEntrega.usuario_id == user.id)
        ).first()
        if not direccion:
            continue

        forma_pago = formas_pago.get(pedido_data["forma_pago"])
        estado_final = estados.get(pedido_data["estado_final"])
        if not forma_pago or not estado_final:
            continue

        total = Decimal("0")
        items_resueltos = []
        for nombre_prod, cantidad in pedido_data["items"]:
            prod = session.exec(
                select(Producto).where(Producto.nombre == nombre_prod, Producto.deleted_at.is_(None))
            ).first()
            if not prod:
                continue
            subtotal = Decimal(str(prod.precio)) * cantidad
            total += subtotal
            items_resueltos.append((prod, cantidad, subtotal))

        pedido = Pedido(
            usuario_id=user.id,
            direccion_entrega_id=direccion.id,
            forma_pago_id=forma_pago.id,
            estado_id=estado_final.id,
            total=total,
            observaciones=pedido_data["observaciones"],
        )
        session.add(pedido)
        session.flush()

        for prod, cantidad, subtotal in items_resueltos:
            session.add(DetallePedido(
                pedido_id=pedido.id,
                producto_id=prod.id,
                producto_nombre=prod.nombre,
                precio_unitario=Decimal(str(prod.precio)),
                cantidad=cantidad,
                subtotal=subtotal,
            ))

        secuencia = [EstadoPedidoCodigo.PENDIENTE] + pedido_data["estados_intermedios"]
        if pedido_data["estado_final"] not in secuencia:
            secuencia.append(pedido_data["estado_final"])

        anterior_id = None
        for codigo in secuencia:
            estado = estados.get(codigo)
            if not estado:
                continue
            session.add(HistorialEstadoPedido(
                pedido_id=pedido.id,
                estado_anterior_id=anterior_id,
                estado_nuevo_id=estado.id,
                usuario_id=user.id,
            ))
            anterior_id = estado.id

        session.flush()


def reset_datos(session: Session) -> None:
    """Limpia pedidos, productos, ingredientes y categorias para re-seedear desde cero."""
    session.exec(delete(HistorialEstadoPedido))
    session.exec(delete(DetallePedido))
    session.exec(delete(Pedido))
    session.exec(delete(ProductoIngrediente))
    session.exec(delete(Producto))
    session.exec(delete(Ingrediente))
    session.exec(delete(Categoria))
    session.flush()
    print("reset: tablas limpiadas")


def main(reset: bool = False) -> None:
    create_db_and_tables()
    with Session(engine) as session:
        if reset:
            reset_datos(session)
        seed_roles(session)
        seed_estados_pedido(session)
        seed_formas_pago(session)
        categorias = seed_categorias(session)
        ingredientes = seed_ingredientes(session)
        seed_productos(session, categorias, ingredientes)
        seed_usuario_admin(session)
        seed_usuarios_staff(session)
        seed_pedidos(session)
        session.commit()
        print("seed completo")


if __name__ == "__main__":
    main(reset="--reset" in sys.argv)
