from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

# URL de conexión a PostgreSQL desde variable de entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234postgres@localhost:5432/parcial_prog4"
)

# Motor de base de datos con echo para ver SQL en consola
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """Crea todas las tablas en la base de datos"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency para obtener sesión de base de datos"""
    with Session(engine) as session:
        yield session
