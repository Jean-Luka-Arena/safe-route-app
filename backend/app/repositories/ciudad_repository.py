from collections import defaultdict

from app.db.models import Ubicacion, Conexion, Incidente
from app.tda_grafo.grafo_ciudad import GrafoCiudad

SEGURIDAD_MINIMA = 0
SEGURIDAD_MAXIMA = 10


def obtener_ciudad(sesion):
    """arma un GrafoCiudad leyendo ubicaciones y conexiones desde la
    base de datos, aplicando la seguridad efectiva de cada calle segun
    sus incidentes reportados
    """
    ciudad = GrafoCiudad()

    for ubicacion in sesion.query(Ubicacion).all():
        ciudad.agregar_ubicacion(ubicacion.id)

    gravedad_por_conexion = _sumar_gravedad_de_incidentes(sesion)

    for conexion in sesion.query(Conexion).all():
        seguridad_efectiva = _aplicar_incidentes(
            conexion.nivel_seguridad,
            gravedad_por_conexion.get(conexion.id, 0),
        )
        ciudad.agregar_calle(
            conexion.origen_id,
            conexion.destino_id,
            distancia=conexion.distancia,
            seguridad=seguridad_efectiva,
        )

    return ciudad


def _sumar_gravedad_de_incidentes(sesion):
    totales = defaultdict(float)
    for incidente in sesion.query(Incidente).all():
        totales[incidente.conexion_id] += incidente.gravedad
    return totales


def _aplicar_incidentes(seguridad_base, gravedad_acumulada):
    seguridad = seguridad_base - gravedad_acumulada
    return max(SEGURIDAD_MINIMA, min(SEGURIDAD_MAXIMA, seguridad))
