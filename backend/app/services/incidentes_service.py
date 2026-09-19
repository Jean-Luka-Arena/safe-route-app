import datetime
from datetime import timezone

from app.db.models import Conexion, Incidente
from app.schemas import TipoIncidente


class ConexionInexistente(Exception):
    def __init__(self, conexion_id):
        self.conexion_id = conexion_id
        super().__init__(f"la calle con id {conexion_id} no existe")


class IncidenteInexistente(Exception):
    def __init__(self, incidente_id):
        self.incidente_id = incidente_id
        super().__init__(f"el incidente con id {incidente_id} no existe")


class NoAutorizado(Exception):
    pass


GRAVEDAD_POR_TIPO = {
    TipoIncidente.ROBO: 8,
    TipoIncidente.ACCIDENTE: 7,
    TipoIncidente.CALLE_BLOQUEADA: 6,
    TipoIncidente.ZONA_OSCURA: 4,
}


def reportar_incidente(sesion, conexion_id, usuario_id, tipo, fecha=None):
    conexion = sesion.get(Conexion, conexion_id)
    if conexion is None:
        raise ConexionInexistente(conexion_id)

    incidente = Incidente(
        conexion_id=conexion_id,
        usuario_id=usuario_id,
        tipo=tipo.value,
        gravedad=GRAVEDAD_POR_TIPO[tipo],
        fecha=fecha or datetime.datetime.now(timezone.utc),
    )
    sesion.add(incidente)
    sesion.commit()
    sesion.refresh(incidente)

    return incidente


def borrar_incidente(sesion, incidente_id, usuario_id):
    incidente = sesion.get(Incidente, incidente_id)
    if incidente is None:
        raise IncidenteInexistente(incidente_id)

    if incidente.usuario_id != usuario_id:
        raise NoAutorizado()

    sesion.delete(incidente)
    sesion.commit()


def listar_incidentes_de_usuario(sesion, usuario_id):
    return (
        sesion.query(Incidente)
        .filter_by(usuario_id=usuario_id)
        .order_by(Incidente.fecha.desc())
        .all()
    )
