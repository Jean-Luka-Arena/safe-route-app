import pytest
from grafo import Grafo


# ---------- FIXTURES ----------


@pytest.fixture
def grafo_vacio():
    return Grafo()


@pytest.fixture
def grafo_simple():
    g = Grafo()
    for v in ["A", "B", "C"]:
        g.agregar_vertice(v)
    return g


@pytest.fixture
def grafo_con_aristas():
    g = Grafo()
    for v in ["A", "B", "C"]:
        g.agregar_vertice(v)
    g.agregar_arista("A", "B", 5)
    g.agregar_arista("B", "C", 3)
    return g


# ---------- TESTS BASICOS ----------


def test_grafo_inicial_vacio(grafo_vacio):
    assert grafo_vacio.obtener_vertices() == []


def test_agregar_vertice(grafo_vacio):
    grafo_vacio.agregar_vertice("A")
    assert "A" in grafo_vacio.obtener_vertices()


def test_no_agrega_vertice_repetido(grafo_vacio):
    grafo_vacio.agregar_vertice("A")
    grafo_vacio.agregar_vertice("A")
    assert len(grafo_vacio.obtener_vertices()) == 1


# ---------- ARISTAS ----------


def test_agregar_arista(grafo_simple):
    grafo_simple.agregar_arista("A", "B", 10)
    assert grafo_simple.estan_unidos("A", "B")
    assert grafo_simple.estan_unidos("B", "A")


def test_peso_arista(grafo_simple):
    grafo_simple.agregar_arista("A", "B", 7)
    assert grafo_simple.peso_arista("A", "B") == 7


def test_borrar_arista(grafo_con_aristas):
    grafo_con_aristas.borrar_arista("A", "B")
    assert not grafo_con_aristas.estan_unidos("A", "B")


def test_borrar_arista_inexistente(grafo_simple):
    with pytest.raises(Exception):
        grafo_simple.borrar_arista("A", "B")


# ---------- VERTICES ----------


def test_borrar_vertice(grafo_con_aristas):
    grafo_con_aristas.borrar_vertice("B")
    assert "B" not in grafo_con_aristas.obtener_vertices()
    assert not grafo_con_aristas.estan_unidos("A", "B")


def test_borrar_vertice_inexistente(grafo_simple):
    with pytest.raises(Exception):
        grafo_simple.borrar_vertice("Z")


# ---------- ADYACENTES ----------


def test_adyacentes(grafo_con_aristas):
    ady = grafo_con_aristas.adyacentes("B")
    assert set(ady) == {"A", "C"}


def test_adyacentes_inexistente(grafo_simple):
    with pytest.raises(Exception):
        grafo_simple.adyacentes("Z")


# ---------- GRAFO DIRIGIDO ----------


def test_grafo_dirigido():
    g = Grafo(es_dirigido=True)
    g.agregar_vertice("A")
    g.agregar_vertice("B")
    g.agregar_arista("A", "B")

    assert g.estan_unidos("A", "B")
    assert not g.estan_unidos("B", "A")


# ---------- VERTICE ALEATORIO ----------


def test_vertice_aleatorio(grafo_simple):
    v = grafo_simple.vertice_aleatorio()
    assert v in grafo_simple.obtener_vertices()


def test_vertice_aleatorio_grafo_vacio():
    g = Grafo()
    assert g.vertice_aleatorio() is None


# ---------- TEST DE VOLUMEN ----------


def test_grafo_grande():
    g = Grafo()
    n = 1000

    # agregar vertices
    for i in range(n):
        g.agregar_vertice(i)

    # conectar en cadena
    for i in range(n - 1):
        g.agregar_arista(i, i + 1, i)

    # chequeos
    assert len(g.obtener_vertices()) == n
    assert g.estan_unidos(0, 1)
    assert g.peso_arista(10, 11) == 10


# ---------- TEST DE CONSISTENCIA ----------


def test_consistencia_tras_borrados():
    g = Grafo()
    for v in ["A", "B", "C", "D"]:
        g.agregar_vertice(v)

    g.agregar_arista("A", "B")
    g.agregar_arista("B", "C")
    g.agregar_arista("C", "D")

    g.borrar_vertice("B")

    assert "B" not in g.obtener_vertices()
    assert not g.estan_unidos("A", "B")
    assert not g.estan_unidos("B", "C")
