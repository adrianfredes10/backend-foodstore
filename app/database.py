from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

# importa modelos para que SQLModel.metadata los registre
import app.models  # noqa: F401, E402


# url postgres desde env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234postgres@localhost:5434/parcial_prog4",
)

# motor; echo solo si SQL_ECHO=true en .env (para debug)
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")
engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def create_db_and_tables():
    # crea tablas si no existen
    SQLModel.metadata.create_all(engine)


def get_session():
    # generador para dependency injection (si lo usas)
    with Session(engine) as session:
        yield session
