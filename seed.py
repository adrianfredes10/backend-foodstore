"""
script de seeding inserta datos de prueba
correr manual: python seed.py
si ya existen no los duplica
"""
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models.categoria import Categoria
from app.models.ingrediente import Ingrediente, ProductoIngrediente
from app.models.producto import Producto
from app.seed_obligatorio import (
    seed_estados_pedido,
    seed_formas_pago,
    seed_roles,
    seed_usuario_admin,
)

CATEGORIAS = [
    {"nombre": "Bebidas Calientes", "descripcion": "Cafés, tés e infusiones"},
    {"nombre": "Bebidas Frías",     "descripcion": "Jugos, licuados y frapés"},
    {"nombre": "Comidas",           "descripcion": "Platos principales y snacks"},
    {"nombre": "Postres",           "descripcion": "Dulces, tortas y helados"},
]

INGREDIENTES = [
    {"nombre": "Leche",           "unidad_medida": "ml",       "stock_actual": 10000, "stock_minimo": 2000},
    {"nombre": "Café",            "unidad_medida": "g",        "stock_actual": 3000,  "stock_minimo": 500},
    {"nombre": "Azúcar",          "unidad_medida": "g",        "stock_actual": 5000,  "stock_minimo": 1000},
    {"nombre": "Harina",          "unidad_medida": "g",        "stock_actual": 8000,  "stock_minimo": 1500},
    {"nombre": "Huevo",           "unidad_medida": "unidades", "stock_actual": 60,    "stock_minimo": 12},
    {"nombre": "Manteca",         "unidad_medida": "g",        "stock_actual": 2000,  "stock_minimo": 500},
    {"nombre": "Cacao",           "unidad_medida": "g",        "stock_actual": 1500,  "stock_minimo": 300},
    {"nombre": "Crema",           "unidad_medida": "ml",       "stock_actual": 3000,  "stock_minimo": 500},
    {"nombre": "Frutillas",       "unidad_medida": "g",        "stock_actual": 2000,  "stock_minimo": 400},
    {"nombre": "Jugo de naranja", "unidad_medida": "ml",       "stock_actual": 4000,  "stock_minimo": 800},
]

# nombre, descripcion, precio, disponible, categoria (primera se usa como FK 1:N), ingredientes
PRODUCTOS = [
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
        "nombre": "Medialunas",
        "descripcion": "3 medialunas de manteca artesanales",
        "precio": 400.00,
        "disponible": True,
        "categoria": "Comidas",
        "ingredientes": [
            {"nombre": "Harina",  "cantidad": 200},
            {"nombre": "Manteca", "cantidad": 80},
            {"nombre": "Azúcar",  "cantidad": 30},
            {"nombre": "Huevo",   "cantidad": 2},
        ],
    },
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


def main():
    create_db_and_tables()
    with Session(engine) as session:
        seed_roles(session)
        seed_estados_pedido(session)
        seed_formas_pago(session)
        categorias = seed_categorias(session)
        ingredientes = seed_ingredientes(session)
        seed_productos(session, categorias, ingredientes)
        seed_usuario_admin(session)
        session.commit()


if __name__ == "__main__":
    main()
