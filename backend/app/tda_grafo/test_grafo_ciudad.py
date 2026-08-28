import pytest
from grafo_ciudad import GrafoCiudad

# ---------- FIXTURES ----------


@pytest.fixture
def ciudad_vacia():
    return GrafoCiudad()


@pytest.fixture
def ciudad_con_calles():
    c = GrafoCiudad()
    for u in ["A", "B", "C"]:
        c.agregar_ubicacion(u)
    c.agregar_calle("A", "B", distancia=500, seguridad=8)
    c.agregar_calle("B", "C", distancia=300, seguridad=4)
    return c


# ---------- UBICACIONES ----------


def test_ciudad_vacia_sin_ubicaciones(ciudad_vacia):
    assert ciudad_vacia.obtener_ubicaciones() == []


def test_agregar_ubicacion(ciudad_vacia):
    ciudad_vacia.agregar_ubicacion("A")
    assert ciudad_vacia.existe_ubicacion("A")


def test_ubicacion_inexistente(ciudad_vacia):
    assert not ciudad_vacia.existe_ubicacion("Z")


# ---------- CALLES ----------


def test_agregar_calle_conecta_ubicaciones(ciudad_con_calles):
    assert ciudad_con_calles.hay_calle("A", "B")
    assert ciudad_con_calles.hay_calle("B", "A")  # no dirigido por defecto


def test_obtener_atributos_de_una_calle(ciudad_con_calles):
    atributos = ciudad_con_calles.obtener_atributos("A", "B")
    assert atributos.distancia == 500
    assert atributos.seguridad == 8


def test_no_hay_calle_entre_ubicaciones_no_conectadas(ciudad_con_calles):
    assert not ciudad_con_calles.hay_calle("A", "C")


def test_agregar_calle_con_ubicacion_inexistente_falla(ciudad_vacia):
    ciudad_vacia.agregar_ubicacion("A")
    with pytest.raises(Exception):
        ciudad_vacia.agregar_calle("A", "Z", distancia=100, seguridad=5)


def test_agregar_calle_con_seguridad_invalida_falla(ciudad_vacia):
    ciudad_vacia.agregar_ubicacion("A")
    ciudad_vacia.agregar_ubicacion("B")
    with pytest.raises(ValueError):
        ciudad_vacia.agregar_calle("A", "B", distancia=100, seguridad=99)


# ---------- CALLES DESDE UNA UBICACION ----------


def test_calles_desde_ubicacion(ciudad_con_calles):
    assert set(ciudad_con_calles.calles_desde("B")) == {"A", "C"}


# ---------- GRAFO DIRIGIDO ----------


def test_ciudad_dirigida():
    c = GrafoCiudad(es_dirigido=True)
    c.agregar_ubicacion("A")
    c.agregar_ubicacion("B")
    c.agregar_calle("A", "B", distancia=200, seguridad=6)

    assert c.hay_calle("A", "B")
    assert not c.hay_calle("B", "A")
