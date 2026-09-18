import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Ubicacion, Conexion, Usuario
from app.schemas import TipoIncidente
from app.services.incidentes_service import (
    reportar_incidente,
    ConexionInexistente,
    GRAVEDAD_POR_TIPO,
)


@pytest.fixture
def sesion_con_calle_y_usuario():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Sesion = sessionmaker(bind=engine)
    sesion = Sesion()

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
    sesion.add(Usuario(id=1, email="a@a.com", password_hash="x"))
    sesion.commit()

    yield sesion
    sesion.close()


def test_reportar_incidente_asigna_gravedad_segun_tipo(sesion_con_calle_y_usuario):
    incidente = reportar_incidente(sesion_con_calle_y_usuario, 1, 1, TipoIncidente.ROBO)
    assert incidente.gravedad == GRAVEDAD_POR_TIPO[TipoIncidente.ROBO]
    assert incidente.conexion_id == 1
    assert incidente.usuario_id == 1
    assert incidente.tipo == "robo"


@pytest.mark.parametrize("tipo", list(TipoIncidente))
def test_gravedad_coincide_con_la_tabla_para_todos_los_tipos(
    sesion_con_calle_y_usuario, tipo
):
    incidente = reportar_incidente(sesion_con_calle_y_usuario, 1, 1, tipo)
    assert incidente.gravedad == GRAVEDAD_POR_TIPO[tipo]


def test_conexion_inexistente_lanza_excepcion(sesion_con_calle_y_usuario):
    with pytest.raises(ConexionInexistente):
        reportar_incidente(sesion_con_calle_y_usuario, 999, 1, TipoIncidente.ROBO)


def test_incidente_queda_persistido_con_su_usuario(sesion_con_calle_y_usuario):
    reportar_incidente(sesion_con_calle_y_usuario, 1, 1, TipoIncidente.ACCIDENTE)

    from app.db.models import Incidente

    guardados = sesion_con_calle_y_usuario.query(Incidente).all()
    assert len(guardados) == 1
    assert guardados[0].usuario_id == 1
