from grafo import Grafo
from atributos_calle import AtributosCalle


class GrafoCiudad:
    """Modela una ciudad como un grafo de ubicaciones conectadas por calles,
    donde cada calle tiene una distancia y un nivel de seguridad.

    Compone un Grafo genérico en vez de heredar de él (composición sobre
    herencia), para que la lógica de dominio ("calle", "ubicación") no
    quede acoplada al TDA genérico de grafos, que no sabe nada de
    distancias ni seguridad.
    """

    def __init__(self, es_dirigido=False):
        self._grafo = Grafo(es_dirigido=es_dirigido)

    def agregar_ubicacion(self, ubicacion):
        self._grafo.agregar_vertice(ubicacion)

    def existe_ubicacion(self, ubicacion):
        return ubicacion in self._grafo.obtener_vertices()

    def obtener_ubicaciones(self):
        return self._grafo.obtener_vertices()

    def agregar_calle(self, origen, destino, distancia, seguridad):
        atributos = AtributosCalle(distancia, seguridad)
        self._grafo.agregar_arista(origen, destino, atributos)

    def obtener_atributos(self, origen, destino):
        return self._grafo.peso_arista(origen, destino)

    def hay_calle(self, origen, destino):
        return self._grafo.estan_unidos(origen, destino)

    def calles_desde(self, ubicacion):
        return self._grafo.adyacentes(ubicacion)

    def __str__(self):
        return str(self._grafo)
