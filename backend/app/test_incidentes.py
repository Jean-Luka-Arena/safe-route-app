import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, obtener_sesion
from app.db.models import Ubicacion, Conexion, Usuario
from app.dependencias import obtener_usuario_actual
from app.incidentes import router as incidentes_router
from app.services.incidentes_service import GRAVEDAD_POR_TIPO
from app.schemas import TipoIncidente


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(incidentes_router)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SesionDePrueba = sessionmaker(bind=engine, expire_on_commit=False)

    sesion = SesionDePrueba()
    sesion.add_all(
        [
            Ubicacion(id=1, latitud=0, longitud=0),
            Ubicacion(id=2, latitud=0, longitud=0),
        ]
    )
    sesion.flush()
    sesion.add(
        Conexion(id=1, origen_id=1, destino_id=2, distancia=100, nivel_seguridad=9)
    )
    usuario = Usuario(id=1, email="a@a.com", password_hash="x")
    sesion.add(usuario)
    sesion.commit()
    sesion.close()

    def sesion_de_prueba():
        s = SesionDePrueba()
        try:
            yield s
        finally:
            s.close()

    def usuario_de_prueba():
        return usuario

    app.dependency_overrides[obtener_sesion] = sesion_de_prueba
    app.dependency_overrides[obtener_usuario_actual] = usuario_de_prueba
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_reportar_incidente_devuelve_201_y_no_acepta_gravedad_del_cliente(client):
    respuesta = client.post(
        "/incidents",
        json={"conexion_id": 1, "tipo": "robo", "gravedad": 999},
    )
    assert respuesta.status_code == 201
    data = respuesta.json()
    assert data["gravedad"] == GRAVEDAD_POR_TIPO[TipoIncidente.ROBO]
    assert data["usuario_id"] == 1
    assert "id" in data
    assert "fecha" in data


def test_tipo_invalido_devuelve_422(client):
    respuesta = client.post("/incidents", json={"conexion_id": 1, "tipo": "marciano"})
    assert respuesta.status_code == 422


def test_calle_inexistente_devuelve_404(client):
    respuesta = client.post("/incidents", json={"conexion_id": 999, "tipo": "robo"})
    assert respuesta.status_code == 404


def test_sin_autenticar_devuelve_401():
    app = FastAPI()
    app.include_router(incidentes_router)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Sesion = sessionmaker(bind=engine)

    def sesion_de_prueba():
        s = Sesion()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[obtener_sesion] = sesion_de_prueba
    cliente_sin_login = TestClient(app)

    respuesta = cliente_sin_login.post(
        "/incidents", json={"conexion_id": 1, "tipo": "robo"}
    )
    assert respuesta.status_code == 401


def test_borrar_incidente_propio_devuelve_204(client):
    creado = client.post("/incidents", json={"conexion_id": 1, "tipo": "robo"}).json()
    respuesta = client.delete(f"/incidents/{creado['id']}")
    assert respuesta.status_code == 204


def test_borrar_incidente_de_otro_usuario_devuelve_403(client):
    creado = client.post("/incidents", json={"conexion_id": 1, "tipo": "robo"}).json()

    otro_usuario = Usuario(id=2, email="b@b.com", password_hash="x")
    client.app.dependency_overrides[obtener_usuario_actual] = lambda: otro_usuario

    respuesta = client.delete(f"/incidents/{creado['id']}")
    assert respuesta.status_code == 403


def test_borrar_incidente_inexistente_devuelve_404(client):
    respuesta = client.delete("/incidents/999")
    assert respuesta.status_code == 404
