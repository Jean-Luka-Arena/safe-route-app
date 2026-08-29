import pytest
from app.tda_grafo.grafo_ciudad import GrafoCiudad
from app.algorithms.dijkstra import dijkstra
from app.tda_grafo.excepciones import UbicacionInexistente

# ---------- FUNCIONES DE COSTO DE PRUEBA ----------


def costo_por_distancia(atributos):
    return atributos.distancia


def costo_por_riesgo(atributos):
    # a mayor seguridad, menor riesgo
    return 10 - atributos.seguridad


# ---------- FIXTURES ----------


@pytest.fixture
def ciudad_lineal():
    # A --5-- B --3-- C
    c = GrafoCiudad()
    for u in ["A", "B", "C"]:
        c.agregar_ubicacion(u)
    c.agregar_calle("A", "B", distancia=5, seguridad=8)
    c.agregar_calle("B", "C", distancia=3, seguridad=8)
    return c


@pytest.fixture
def ciudad_con_dos_caminos():
    #      A
    #    /   \
    #  10      1
    #   \     /
    #     B--C
    # camino corto: A-B (10) -> total 10 directo a B no hay, dejamos con dos rutas a D
    #
    # A -> B (dist 10, seguridad 9)
    # A -> C (dist 1,  seguridad 2)
    # B -> D (dist 1,  seguridad 9)
    # C -> D (dist 1,  seguridad 2)
    c = GrafoCiudad()
    for u in ["A", "B", "C", "D"]:
        c.agregar_ubicacion(u)
    c.agregar_calle("A", "B", distancia=10, seguridad=9)
    c.agregar_calle("A", "C", distancia=1, seguridad=2)
    c.agregar_calle("B", "D", distancia=1, seguridad=9)
    c.agregar_calle("C", "D", distancia=1, seguridad=2)
    return c


@pytest.fixture
def ciudad_desconectada():
    c = GrafoCiudad()
    for u in ["A", "B", "C"]:
        c.agregar_ubicacion(u)
    c.agregar_calle("A", "B", distancia=5, seguridad=5)
    # C queda aislada
    return c


# ---------- CASOS BASICOS ----------


def test_camino_directo(ciudad_lineal):
    camino, costo = dijkstra(ciudad_lineal, "A", "C", costo_por_distancia)
    assert camino == ["A", "B", "C"]
    assert costo == 8


def test_origen_igual_a_destino(ciudad_lineal):
    camino, costo = dijkstra(ciudad_lineal, "A", "A", costo_por_distancia)
    assert camino == ["A"]
    assert costo == 0


def test_ubicacion_origen_inexistente(ciudad_lineal):
    with pytest.raises(UbicacionInexistente):
        dijkstra(ciudad_lineal, "Z", "A", costo_por_distancia)


def test_ubicacion_destino_inexistente(ciudad_lineal):
    with pytest.raises(UbicacionInexistente):
        dijkstra(ciudad_lineal, "A", "Z", costo_por_distancia)


def test_sin_camino_posible(ciudad_desconectada):
    camino, costo = dijkstra(ciudad_desconectada, "A", "C", costo_por_distancia)
    assert camino is None
    assert costo == float("inf")


# ---------- ELIGE EL MEJOR CAMINO SEGUN EL COSTO ----------


def test_elige_camino_mas_corto_por_distancia(ciudad_con_dos_caminos):
    # A-C-D (1+1=2) es mas corto que A-B-D (10+1=11)
    camino, costo = dijkstra(ciudad_con_dos_caminos, "A", "D", costo_por_distancia)
    assert camino == ["A", "C", "D"]
    assert costo == 2


def test_elige_camino_mas_seguro_por_riesgo(ciudad_con_dos_caminos):
    # riesgo A-B-D = (10-9)+(10-9) = 2
    # riesgo A-C-D = (10-2)+(10-2) = 16
    camino, costo = dijkstra(ciudad_con_dos_caminos, "A", "D", costo_por_riesgo)
    assert camino == ["A", "B", "D"]
    assert costo == 2


def test_mismo_grafo_distintos_resultados_segun_funcion_costo(
    ciudad_con_dos_caminos,
):
    # la misma ciudad da caminos distintos segun el criterio: prueba de
    # que dijkstra es realmente generico respecto de la funcion de costo.
    camino_corto, _ = dijkstra(ciudad_con_dos_caminos, "A", "D", costo_por_distancia)
    camino_seguro, _ = dijkstra(ciudad_con_dos_caminos, "A", "D", costo_por_riesgo)
    assert camino_corto != camino_seguro
