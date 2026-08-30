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
    """Cliente de pruebas con una base SQLite en memoria "inyectada"
    en lugar de la Postgres real, via dependency_overrides de FastAPI.

    StaticPool + check_same_thread=False son necesarios para que todas
    las conexiones (la que siembra los datos y la que usa el endpoint)
    compartan la misma base en memoria: por defecto, SQLite abre una
    base distinta por cada conexion nueva.

    Datos de prueba (mismo grafo usado en los tests de dijkstra):
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
            Conexion(origen_id=1, destino_id=2, distancia=10, nivel_seguridad=9),
            Conexion(origen_id=1, destino_id=3, distancia=1, nivel_seguridad=2),
            Conexion(origen_id=2, destino_id=4, distancia=1, nivel_seguridad=9),
            Conexion(origen_id=3, destino_id=4, distancia=1, nivel_seguridad=2),
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


# ---------- CASOS EXITOSOS ----------


def test_ruta_mas_corta(client):
    respuesta = client.get(
        "/route", params={"origin": 1, "destination": 4, "criteria": "corta"}
    )
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["ruta"] == [1, 3, 4]


def test_ruta_mas_segura(client):
    respuesta = client.get(
        "/route", params={"origin": 1, "destination": 4, "criteria": "segura"}
    )
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["ruta"] == [1, 2, 4]


def test_ruta_balanceada(client):
    respuesta = client.get(
        "/route",
        params={
            "origin": 1,
            "destination": 4,
            "criteria": "balanceada",
            "alpha": 0.5,
            "beta": 0.5,
        },
    )
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["ruta"][0] == 1
    assert data["ruta"][-1] == 4


def test_respuesta_incluye_los_campos_esperados(client):
    respuesta = client.get(
        "/route", params={"origin": 1, "destination": 2, "criteria": "corta"}
    )
    data = respuesta.json()
    assert set(data.keys()) == {
        "ruta",
        "distancia_total",
        "seguridad_promedio",
        "costo_total",
    }


# ---------- ERRORES DEL CLIENTE (400) ----------


def test_criterio_invalido_devuelve_400(client):
    respuesta = client.get(
        "/route", params={"origin": 1, "destination": 2, "criteria": "mas_linda"}
    )
    assert respuesta.status_code == 400


def test_balanceada_sin_alpha_beta_devuelve_400(client):
    respuesta = client.get(
        "/route", params={"origin": 1, "destination": 2, "criteria": "balanceada"}
    )
    assert respuesta.status_code == 400


def test_falta_parametro_obligatorio_devuelve_422(client):
    respuesta = client.get("/route", params={"origin": 1, "criteria": "corta"})
    assert respuesta.status_code == 422


# ---------- ERRORES DE RECURSO (404) ----------


def test_origen_inexistente_devuelve_404(client):
    respuesta = client.get(
        "/route", params={"origin": 999, "destination": 1, "criteria": "corta"}
    )
    assert respuesta.status_code == 404


def test_destino_inexistente_devuelve_404(client):
    respuesta = client.get(
        "/route", params={"origin": 1, "destination": 999, "criteria": "corta"}
    )
    assert respuesta.status_code == 404
