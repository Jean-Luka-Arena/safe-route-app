from app.db.models import Ubicacion, Conexion
from app.tda_grafo.grafo_ciudad import GrafoCiudad


def obtener_ciudad(sesion):
    """Arma un GrafoCiudad leyendo ubicaciones y conexiones desde la
    base de datos.
    """
    ciudad = GrafoCiudad()

    for ubicacion in sesion.query(Ubicacion).all():
        ciudad.agregar_ubicacion(ubicacion.id)

    for conexion in sesion.query(Conexion).all():
        ciudad.agregar_calle(
            conexion.origen_id,
            conexion.destino_id,
            distancia=conexion.distancia,
            seguridad=conexion.nivel_seguridad,
        )

    return ciudad
