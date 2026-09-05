import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Ubicacion, Conexion, Incidente
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


# ---------- SEGURIDAD DINAMICA POR INCIDENTES ----------


def test_sin_incidentes_usa_la_seguridad_base(sesion_con_datos):
    ciudad = obtener_ciudad(sesion_con_datos)
    assert ciudad.obtener_atributos(1, 2).seguridad == 8


def test_un_incidente_baja_la_seguridad_efectiva(sesion_con_datos):
    conexion = sesion_con_datos.query(Conexion).first()
    sesion_con_datos.add(Incidente(conexion_id=conexion.id, tipo="robo", gravedad=3))
    sesion_con_datos.commit()

    ciudad = obtener_ciudad(sesion_con_datos)
    # seguridad base 8, incidente de gravedad 3 -> 5
    assert ciudad.obtener_atributos(1, 2).seguridad == 5


def test_varios_incidentes_se_acumulan(sesion_con_datos):
    conexion = sesion_con_datos.query(Conexion).first()
    sesion_con_datos.add_all(
        [
            Incidente(conexion_id=conexion.id, tipo="robo", gravedad=3),
            Incidente(conexion_id=conexion.id, tipo="zona_oscura", gravedad=2),
        ]
    )
    sesion_con_datos.commit()

    ciudad = obtener_ciudad(sesion_con_datos)
    assert ciudad.obtener_atributos(1, 2).seguridad == 3


def test_la_seguridad_efectiva_no_baja_de_cero(sesion_con_datos):
    conexion = sesion_con_datos.query(Conexion).first()
    sesion_con_datos.add(
        Incidente(conexion_id=conexion.id, tipo="accidente", gravedad=100)
    )
    sesion_con_datos.commit()

    ciudad = obtener_ciudad(sesion_con_datos)
    assert ciudad.obtener_atributos(1, 2).seguridad == 0


def test_incidente_en_una_calle_no_afecta_a_otra(sesion_vacia):
    a = Ubicacion(id=1, latitud=0, longitud=0)
    b = Ubicacion(id=2, latitud=0, longitud=0)
    c = Ubicacion(id=3, latitud=0, longitud=0)
    sesion_vacia.add_all([a, b, c])
    sesion_vacia.flush()

    conexion_ab = Conexion(origen_id=1, destino_id=2, distancia=100, nivel_seguridad=8)
    conexion_ac = Conexion(origen_id=1, destino_id=3, distancia=100, nivel_seguridad=8)
    sesion_vacia.add_all([conexion_ab, conexion_ac])
    sesion_vacia.flush()

    sesion_vacia.add(Incidente(conexion_id=conexion_ab.id, tipo="robo", gravedad=5))
    sesion_vacia.commit()

    ciudad = obtener_ciudad(sesion_vacia)
    assert ciudad.obtener_atributos(1, 2).seguridad == 3  # afectada
    assert ciudad.obtener_atributos(1, 3).seguridad == 8  # sin cambios
