import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, obtener_sesion
from app.db.models import Ubicacion


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SesionDePrueba = sessionmaker(bind=engine)

    sesion = SesionDePrueba()
    sesion.add_all(
        [
            Ubicacion(id=1, latitud=-34.60, longitud=-58.38),
            Ubicacion(id=2, latitud=-34.61, longitud=-58.39),
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


def test_listar_ubicaciones(client):
    respuesta = client.get("/locations")
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["latitud"] == -34.60
    assert data[0]["longitud"] == -58.38


def test_listar_ubicaciones_vacio_si_no_hay_datos():
    from sqlalchemy import create_engine as ce
    from sqlalchemy.orm import sessionmaker as sm

    engine = ce(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Sesion = sm(bind=engine)

    def sesion_de_prueba():
        s = Sesion()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[obtener_sesion] = sesion_de_prueba
    client = TestClient(app)
    respuesta = client.get("/locations")
    assert respuesta.status_code == 200
    assert respuesta.json() == []
    app.dependency_overrides.clear()
