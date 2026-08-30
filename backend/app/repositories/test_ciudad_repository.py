import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Ubicacion, Conexion
from app.repositories.ciudad_repository import obtener_ciudad


@pytest.fixture
def sesion_vacia():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Sesion = sessionmaker(bind=engine)
    sesion = Sesion()
    yield sesion
    sesion.close()


@pytest.fixture
def sesion_con_datos(sesion_vacia):
    a = Ubicacion(id=1, latitud=0, longitud=0)
    b = Ubicacion(id=2, latitud=1, longitud=1)
    sesion_vacia.add_all([a, b])
    sesion_vacia.flush()
    sesion_vacia.add(
        Conexion(origen_id=1, destino_id=2, distancia=500, nivel_seguridad=8)
    )
    sesion_vacia.commit()
    return sesion_vacia


def test_ciudad_vacia_si_no_hay_datos(sesion_vacia):
    ciudad = obtener_ciudad(sesion_vacia)
    assert ciudad.obtener_ubicaciones() == []


def test_carga_las_ubicaciones(sesion_con_datos):
    ciudad = obtener_ciudad(sesion_con_datos)
    assert ciudad.existe_ubicacion(1)
    assert ciudad.existe_ubicacion(2)


def test_carga_las_calles_con_sus_atributos(sesion_con_datos):
    ciudad = obtener_ciudad(sesion_con_datos)
    atributos = ciudad.obtener_atributos(1, 2)
    assert atributos.distancia == 500
    assert atributos.seguridad == 8
