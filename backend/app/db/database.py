import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://safe_route:safe_route@localhost:5433/safe_route",
)

SECRET_KEY = os.environ.get("SECRET_KEY", "cambiar-esto-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def obtener_sesion():
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()
