import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Ubicacion, Conexion


@pytest.fixture
def sesion():
    """Sesión contra una base SQLite en memoria, solo para validar el
    mapeo de los modelos sin depender de tener Postgres corriendo.
    La base real (Postgres) se prueba aparte, de forma manual, contra
    el docker-compose.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SesionDePrueba = sessionmaker(bind=engine)
    sesion = SesionDePrueba()
    yield sesion
    sesion.close()


def test_crear_y_leer_una_ubicacion(sesion):
    ubicacion = Ubicacion(latitud=-34.6037, longitud=-58.3816)
    sesion.add(ubicacion)
    sesion.commit()

    leida = sesion.query(Ubicacion).first()
    assert leida.latitud == -34.6037
    assert leida.longitud == -58.3816
    assert leida.id is not None


def test_crear_una_conexion_entre_dos_ubicaciones(sesion):
    a = Ubicacion(latitud=-34.60, longitud=-58.38)
    b = Ubicacion(latitud=-34.61, longitud=-58.39)
    sesion.add_all([a, b])
    sesion.commit()

    conexion = Conexion(
        origen_id=a.id,
        destino_id=b.id,
        distancia=500,
        nivel_seguridad=8,
    )
    sesion.add(conexion)
    sesion.commit()

    leida = sesion.query(Conexion).first()
    assert leida.origen_id == a.id
    assert leida.destino_id == b.id
    assert leida.distancia == 500
    assert leida.nivel_seguridad == 8


def test_relacion_origen_destino_devuelve_las_ubicaciones(sesion):
    a = Ubicacion(latitud=-34.60, longitud=-58.38)
    b = Ubicacion(latitud=-34.61, longitud=-58.39)
    sesion.add_all([a, b])
    sesion.commit()

    conexion = Conexion(
        origen_id=a.id, destino_id=b.id, distancia=100, nivel_seguridad=5
    )
    sesion.add(conexion)
    sesion.commit()

    leida = sesion.query(Conexion).first()
    assert leida.origen.id == a.id
    assert leida.destino.id == b.id


def test_varias_conexiones_desde_la_misma_ubicacion(sesion):
    a = Ubicacion(latitud=0, longitud=0)
    b = Ubicacion(latitud=1, longitud=1)
    c = Ubicacion(latitud=2, longitud=2)
    sesion.add_all([a, b, c])
    sesion.commit()

    sesion.add_all(
        [
            Conexion(origen_id=a.id, destino_id=b.id, distancia=10, nivel_seguridad=5),
            Conexion(origen_id=a.id, destino_id=c.id, distancia=20, nivel_seguridad=3),
        ]
    )
    sesion.commit()

    conexiones = sesion.query(Conexion).filter_by(origen_id=a.id).all()
    assert len(conexiones) == 2
