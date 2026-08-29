from app.algorithms.dijkstra import dijkstra
from app.algorithms.costos import (
    costo_distancia,
    costo_seguridad,
    hacer_costo_balanceado,
)

CRITERIOS_VALIDOS = ("corta", "segura", "balanceada")


class ResultadoRuta:

    def __init__(self, camino, distancia_total, seguridad_promedio, costo_total):
        self.camino = camino
        self.distancia_total = distancia_total
        self.seguridad_promedio = seguridad_promedio
        self.costo_total = costo_total

    def existe_camino(self):
        return self.camino is not None

    def to_dict(self):
        return {
            "ruta": self.camino,
            "distancia_total": self.distancia_total,
            "seguridad_promedio": self.seguridad_promedio,
            "costo_total": self.costo_total,
        }

    def __repr__(self):
        return (
            f"ResultadoRuta(camino={self.camino}, "
            f"distancia_total={self.distancia_total}, "
            f"seguridad_promedio={self.seguridad_promedio}, "
            f"costo_total={self.costo_total})"
        )


def _elegir_funcion_costo(criterio, alpha, beta):
    if criterio == "corta":
        return costo_distancia
    if criterio == "segura":
        return costo_seguridad
    if criterio == "balanceada":
        if alpha is None or beta is None:
            raise ValueError(
                "el criterio 'balanceada' requiere especificar alpha y beta"
            )
        return hacer_costo_balanceado(alpha, beta)

    raise ValueError(
        f"criterio '{criterio}' inválido. Debe ser uno de: {CRITERIOS_VALIDOS}"
    )


def _metricas_del_camino(ciudad, camino):
    if len(camino) < 2:
        return 0, 10

    distancia_total = 0
    seguridades = []
    for origen, destino in zip(camino, camino[1:]):
        atributos = ciudad.obtener_atributos(origen, destino)
        distancia_total += atributos.distancia
        seguridades.append(atributos.seguridad)

    seguridad_promedio = sum(seguridades) / len(seguridades)
    return distancia_total, seguridad_promedio


def calcular_ruta(ciudad, origen, destino, criterio, alpha=None, beta=None):
    funcion_costo = _elegir_funcion_costo(criterio, alpha, beta)
    camino, costo_total = dijkstra(ciudad, origen, destino, funcion_costo)

    if camino is None:
        return ResultadoRuta(
            camino=None,
            distancia_total=None,
            seguridad_promedio=None,
            costo_total=None,
        )

    distancia_total, seguridad_promedio = _metricas_del_camino(ciudad, camino)
    return ResultadoRuta(camino, distancia_total, seguridad_promedio, costo_total)
