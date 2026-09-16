import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.services.auth_service import (
    registrar_usuario,
    autenticar_usuario,
    crear_token_acceso,
    obtener_usuario_desde_token,
    EmailYaRegistrado,
    CredencialesInvalidas,
    TokenInvalido,
)


@pytest.fixture
def sesion():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Sesion = sessionmaker(bind=engine)
    s = Sesion()
    yield s
    s.close()


def test_registrar_usuario(sesion):
    usuario = registrar_usuario(sesion, "a@a.com", "12345678")
    assert usuario.id is not None
    assert usuario.email == "a@a.com"
    assert usuario.password_hash != "12345678"


def test_no_permite_email_duplicado(sesion):
    registrar_usuario(sesion, "a@a.com", "12345678")
    with pytest.raises(EmailYaRegistrado):
        registrar_usuario(sesion, "a@a.com", "otraclave123")


def test_autenticar_usuario_correcto(sesion):
    registrar_usuario(sesion, "a@a.com", "12345678")
    usuario = autenticar_usuario(sesion, "a@a.com", "12345678")
    assert usuario.email == "a@a.com"


def test_autenticar_con_password_incorrecta(sesion):
    registrar_usuario(sesion, "a@a.com", "12345678")
    with pytest.raises(CredencialesInvalidas):
        autenticar_usuario(sesion, "a@a.com", "incorrecta")


def test_autenticar_con_email_inexistente(sesion):
    with pytest.raises(CredencialesInvalidas):
        autenticar_usuario(sesion, "noexiste@a.com", "12345678")


def test_token_valido_devuelve_el_usuario(sesion):
    usuario = registrar_usuario(sesion, "a@a.com", "12345678")
    token = crear_token_acceso(usuario)
    obtenido = obtener_usuario_desde_token(sesion, token)
    assert obtenido.id == usuario.id


def test_token_invalido_lanza_excepcion(sesion):
    with pytest.raises(TokenInvalido):
        obtener_usuario_desde_token(sesion, "esto-no-es-un-token-valido")
