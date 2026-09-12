import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, obtener_sesion
from app.db.models import Ubicacion, Conexion
from app.conexiones import router as conexiones_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(conexiones_router)

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
    sesion.flush()
    sesion.add(
        Conexion(id=1, origen_id=1, destino_id=2, distancia=500, nivel_seguridad=8)
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


def test_listar_conexiones(client):
    respuesta = client.get("/connections")
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert len(data) == 1
    assert data[0] == {"id": 1, "origen_id": 1, "destino_id": 2}
