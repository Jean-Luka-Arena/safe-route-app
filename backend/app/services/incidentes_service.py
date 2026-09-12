import datetime
from datetime import timezone

from app.db.models import Conexion, Incidente
from app.schemas import TipoIncidente


class ConexionInexistente(Exception):
    def __init__(self, conexion_id):
        self.conexion_id = conexion_id
        super().__init__(f"la calle con id {conexion_id} no existe")


GRAVEDAD_POR_TIPO = {
    TipoIncidente.ROBO: 8,
    TipoIncidente.ACCIDENTE: 7,
    TipoIncidente.CALLE_BLOQUEADA: 6,
    TipoIncidente.ZONA_OSCURA: 4,
}


def reportar_incidente(sesion, conexion_id, tipo, fecha=None):
    conexion = sesion.get(Conexion, conexion_id)
    if conexion is None:
        raise ConexionInexistente(conexion_id)

    incidente = Incidente(
        conexion_id=conexion_id,
        tipo=tipo.value,
        gravedad=GRAVEDAD_POR_TIPO[tipo],
        fecha=fecha or datetime.datetime.now(timezone.utc),
    )
    sesion.add(incidente)
    sesion.commit()
    sesion.refresh(incidente)

    return incidente
