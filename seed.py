"""
Script de seeding — inserta datos de prueba en la base de datos.
Correr UNA sola vez: python seed.py
Si los datos ya existen, los omite (no falla).
"""
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models.categoria import Categoria, ProductoCategoria
from app.models.ingrediente import Ingrediente, ProductoIngrediente
from app.models.producto import Producto


# ──────────────────────────────────────────
# DATOS DE PRUEBA
# ──────────────────────────────────────────

CATEGORIAS = [
    {"nombre": "Bebidas Calientes", "descripcion": "Cafés, tés e infusiones"},
    {"nombre": "Bebidas Frías",     "descripcion": "Jugos, licuados y frapés"},
    {"nombre": "Comidas",           "descripcion": "Platos principales y snacks"},
    {"nombre": "Postres",           "descripcion": "Dulces, tortas y helados"},
]

INGREDIENTES = [
    {"nombre": "Leche",        "unidad_medida": "ml",       "stock_actual": 10000, "stock_minimo": 2000},
    {"nombre": "Café",         "unidad_medida": "g",        "stock_actual": 3000,  "stock_minimo": 500},
    {"nombre": "Azúcar",       "unidad_medida": "g",        "stock_actual": 5000,  "stock_minimo": 1000},
    {"nombre": "Harina",       "unidad_medida": "g",        "stock_actual": 8000,  "stock_minimo": 1500},
    {"nombre": "Huevo",        "unidad_medida": "unidades",  "stock_actual": 60,    "stock_minimo": 12},
    {"nombre": "Manteca",      "unidad_medida": "g",        "stock_actual": 2000,  "stock_minimo": 500},
    {"nombre": "Cacao",        "unidad_medida": "g",        "stock_actual": 1500,  "stock_minimo": 300},
    {"nombre": "Crema",        "unidad_medida": "ml",       "stock_actual": 3000,  "stock_minimo": 500},
    {"nombre": "Frutillas",    "unidad_medida": "g",        "stock_actual": 2000,  "stock_minimo": 400},
    {"nombre": "Jugo de naranja", "unidad_medida": "ml",   "stock_actual": 4000,  "stock_minimo": 800},
]

# nombre, descripcion, precio, disponible, categorias (nombres), ingredientes (nombre, cantidad)
PRODUCTOS = [
    {
        "nombre": "Cappuccino",
        "descripcion": "Café espresso con leche espumosa",
        "precio": 450.00,
        "disponible": True,
        "categorias": ["Bebidas Calientes"],
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
        "categorias": ["Bebidas Calientes"],
        "ingredientes": [
            {"nombre": "Leche", "cantidad": 250},
            {"nombre": "Café",  "cantidad": 20},
            {"nombre": "Azúcar","cantidad": 10},
        ],
    },
    {
        "nombre": "Licuado de Frutilla",
        "descripcion": "Licuado fresco de frutillas con leche",
        "precio": 500.00,
        "disponible": True,
        "categorias": ["Bebidas Frías"],
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
        "categorias": ["Bebidas Frías"],
        "ingredientes": [
            {"nombre": "Jugo de naranja", "cantidad": 300},
        ],
    },
    {
        "nombre": "Medialunas",
        "descripcion": "3 medialunas de manteca artesanales",
        "precio": 400.00,
        "disponible": True,
        "categorias": ["Comidas", "Postres"],
        "ingredientes": [
            {"nombre": "Harina",   "cantidad": 200},
            {"nombre": "Manteca",  "cantidad": 80},
            {"nombre": "Azúcar",   "cantidad": 30},
            {"nombre": "Huevo",    "cantidad": 2},
        ],
    },
    {
        "nombre": "Torta de Chocolate",
        "descripcion": "Porción de torta húmeda de chocolate",
        "precio": 650.00,
        "disponible": True,
        "categorias": ["Postres"],
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


# ──────────────────────────────────────────
# FUNCIONES DE SEEDING
# ──────────────────────────────────────────

def seed_categorias(session: Session) -> dict[str, Categoria]:
    """Inserta categorías y devuelve un dict {nombre: objeto}"""
    resultado = {}
    for data in CATEGORIAS:
        existing = session.exec(
            select(Categoria).where(
                Categoria.nombre == data["nombre"],
                Categoria.deleted_at.is_(None),
            )
        ).first()

        if existing:
            print(f"  [skip] Categoría '{data['nombre']}' ya existe")
            resultado[data["nombre"]] = existing
        else:
            categoria = Categoria(**data)
            session.add(categoria)
            session.flush()  # para obtener el id
            print(f"  [ok]   Categoría '{data['nombre']}' creada (id={categoria.id})")
            resultado[data["nombre"]] = categoria

    return resultado


def seed_ingredientes(session: Session) -> dict[str, Ingrediente]:
    """Inserta ingredientes y devuelve un dict {nombre: objeto}"""
    resultado = {}
    for data in INGREDIENTES:
        existing = session.exec(
            select(Ingrediente).where(
                Ingrediente.nombre == data["nombre"],
                Ingrediente.deleted_at.is_(None),
            )
        ).first()

        if existing:
            print(f"  [skip] Ingrediente '{data['nombre']}' ya existe")
            resultado[data["nombre"]] = existing
        else:
            ingrediente = Ingrediente(**data)
            session.add(ingrediente)
            session.flush()
            print(f"  [ok]   Ingrediente '{data['nombre']}' creado (id={ingrediente.id})")
            resultado[data["nombre"]] = ingrediente

    return resultado


def seed_productos(
    session: Session,
    categorias: dict[str, Categoria],
    ingredientes: dict[str, Ingrediente],
):
    """Inserta productos con sus relaciones"""
    for data in PRODUCTOS:
        existing = session.exec(
            select(Producto).where(
                Producto.nombre == data["nombre"],
                Producto.deleted_at.is_(None),
            )
        ).first()

        if existing:
            print(f"  [skip] Producto '{data['nombre']}' ya existe")
            continue

        # Crear producto
        producto = Producto(
            nombre=data["nombre"],
            descripcion=data["descripcion"],
            precio=data["precio"],
            disponible=data["disponible"],
        )
        session.add(producto)
        session.flush()  # necesario para obtener el id antes de crear relaciones

        # Asignar categorías
        for nombre_cat in data["categorias"]:
            cat = categorias.get(nombre_cat)
            if not cat:
                print(f"  [warn] Categoría '{nombre_cat}' no encontrada, saltando...")
                continue
            session.add(ProductoCategoria(producto_id=producto.id, categoria_id=cat.id))

        # Asignar ingredientes
        for ing_data in data["ingredientes"]:
            ing = ingredientes.get(ing_data["nombre"])
            if not ing:
                print(f"  [warn] Ingrediente '{ing_data['nombre']}' no encontrado, saltando...")
                continue
            session.add(ProductoIngrediente(
                producto_id=producto.id,
                ingrediente_id=ing.id,
                cantidad=ing_data["cantidad"],
            ))

        print(f"  [ok]   Producto '{data['nombre']}' creado (id={producto.id})")


# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────

def main():
    print("\n🌱 Iniciando seeding...\n")

    # Asegurarse de que las tablas existen
    create_db_and_tables()

    with Session(engine) as session:
        print("📂 Categorías:")
        categorias = seed_categorias(session)

        print("\n🧪 Ingredientes:")
        ingredientes = seed_ingredientes(session)

        print("\n🍕 Productos:")
        seed_productos(session, categorias, ingredientes)

        session.commit()

    print("\n✅ Seeding completado!\n")


if __name__ == "__main__":
    main()
