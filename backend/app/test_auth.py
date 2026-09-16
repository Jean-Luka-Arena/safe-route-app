import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, obtener_sesion
from app.auth import router as auth_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(auth_router)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SesionDePrueba = sessionmaker(bind=engine)

    def sesion_de_prueba():
        s = SesionDePrueba()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[obtener_sesion] = sesion_de_prueba
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_registro_exitoso(client):
    respuesta = client.post(
        "/register", json={"email": "a@a.com", "password": "12345678"}
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["email"] == "a@a.com"


def test_registro_con_email_duplicado(client):
    client.post("/register", json={"email": "a@a.com", "password": "12345678"})
    respuesta = client.post(
        "/register", json={"email": "a@a.com", "password": "otraclave123"}
    )
    assert respuesta.status_code == 400


def test_registro_con_password_corta_devuelve_422(client):
    respuesta = client.post("/register", json={"email": "a@a.com", "password": "123"})
    assert respuesta.status_code == 422


def test_registro_con_email_invalido_devuelve_422(client):
    respuesta = client.post(
        "/register", json={"email": "no-es-un-email", "password": "12345678"}
    )
    assert respuesta.status_code == 422


def test_login_exitoso_devuelve_token(client):
    client.post("/register", json={"email": "a@a.com", "password": "12345678"})
    respuesta = client.post("/login", json={"email": "a@a.com", "password": "12345678"})
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_con_password_incorrecta(client):
    client.post("/register", json={"email": "a@a.com", "password": "12345678"})
    respuesta = client.post(
        "/login", json={"email": "a@a.com", "password": "incorrecta"}
    )
    assert respuesta.status_code == 401


def test_login_con_usuario_inexistente(client):
    respuesta = client.post(
        "/login", json={"email": "noexiste@a.com", "password": "12345678"}
    )
    assert respuesta.status_code == 401
