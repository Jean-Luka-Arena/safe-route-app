import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, obtener_sesion
from app.db.models import Ubicacion, Conexion


@pytest.fixture
def client():
    """Mismos datos base que test_rutas.py:
    1 -> 2 (dist 10, seguridad 9)
    1 -> 3 (dist 1,  seguridad 2)
    2 -> 4 (dist 1,  seguridad 9)
    3 -> 4 (dist 1,  seguridad 2)
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SesionDePrueba = sessionmaker(bind=engine)

    sesion = SesionDePrueba()
    for id_ in [1, 2, 3, 4]:
        sesion.add(Ubicacion(id=id_, latitud=0, longitud=0))
    sesion.flush()
    sesion.add_all(
        [
            Conexion(id=1, origen_id=1, destino_id=2, distancia=10, nivel_seguridad=9),
            Conexion(id=2, origen_id=1, destino_id=3, distancia=1, nivel_seguridad=2),
            Conexion(id=3, origen_id=2, destino_id=4, distancia=1, nivel_seguridad=9),
            Conexion(id=4, origen_id=3, destino_id=4, distancia=1, nivel_seguridad=2),
        ]
    )
    sesion.commit()
    sesion.close()

    def sesion_de_prueba():
        s = SesionDePrueba()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[obtener_sesion] = sesion_de_prueba
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- REPORTAR UN INCIDENTE ----------


def test_reportar_incidente_devuelve_201(client):
    respuesta = client.post(
        "/incidents",
        json={"conexion_id": 1, "tipo": "robo", "gravedad": 5},
    )
    assert respuesta.status_code == 201
    data = respuesta.json()
    assert data["conexion_id"] == 1
    assert data["tipo"] == "robo"
    assert data["gravedad"] == 5
    assert "id" in data
    assert "fecha" in data


def test_reportar_incidente_en_calle_inexistente_devuelve_404(client):
    respuesta = client.post(
        "/incidents",
        json={"conexion_id": 999, "tipo": "robo", "gravedad": 5},
    )
    assert respuesta.status_code == 404


def test_reportar_incidente_con_tipo_invalido_devuelve_422(client):
    respuesta = client.post(
        "/incidents",
        json={"conexion_id": 1, "tipo": "marciano", "gravedad": 5},
    )
    assert respuesta.status_code == 422


def test_reportar_incidente_con_gravedad_fuera_de_rango_devuelve_422(client):
    respuesta = client.post(
        "/incidents",
        json={"conexion_id": 1, "tipo": "robo", "gravedad": 99},
    )
    assert respuesta.status_code == 422


# ---------- EFECTO END-TO-END SOBRE /route ----------


def test_reportar_incidente_cambia_la_ruta_mas_segura(client):
    # calle 3 es 2->4, la mas segura del camino 1-2-4 (seguridad 9)
    antes = client.get(
        "/route", params={"origin": 1, "destination": 4, "criteria": "segura"}
    )
    assert antes.json()["ruta"] == [1, 2, 4]

    # reportamos un robo grave en esa calle
    client.post(
        "/incidents",
        json={"conexion_id": 3, "tipo": "robo", "gravedad": 8},
    )

    despues = client.get(
        "/route", params={"origin": 1, "destination": 4, "criteria": "segura"}
    )
    # ahora la calle 2->4 quedo con seguridad 9-8=1, deja de ser la mas segura
    assert despues.json()["ruta"] != antes.json()["ruta"]
