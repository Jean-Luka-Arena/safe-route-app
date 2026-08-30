from app.db.database import Base, engine
from app.db import models


def crear_tablas():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    crear_tablas()
    print("Tablas creadas correctamente :)")
