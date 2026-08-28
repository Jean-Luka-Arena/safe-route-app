import pytest
from app.tda_grafo.atributos_calle import AtributosCalle

# ---------- CREACION ----------


def test_crear_atributos_validos():
    a = AtributosCalle(distancia=500, seguridad=8)
    assert a.distancia == 500
    assert a.seguridad == 8


def test_distancia_negativa_invalida():
    with pytest.raises(ValueError):
        AtributosCalle(distancia=-10, seguridad=5)


def test_seguridad_fuera_de_rango_invalida():
    with pytest.raises(ValueError):
        AtributosCalle(distancia=100, seguridad=11)
    with pytest.raises(ValueError):
        AtributosCalle(distancia=100, seguridad=-1)


def test_seguridad_en_los_bordes_es_valida():
    AtributosCalle(distancia=100, seguridad=0)
    AtributosCalle(distancia=100, seguridad=10)


# ---------- IGUALDAD ----------


def test_igualdad_entre_atributos_iguales():
    a = AtributosCalle(500, 8)
    b = AtributosCalle(500, 8)
    assert a == b


def test_desigualdad_entre_atributos_distintos():
    a = AtributosCalle(500, 8)
    b = AtributosCalle(500, 7)
    assert a != b


def test_igualdad_con_otro_tipo():
    a = AtributosCalle(500, 8)
    assert a != "no soy un AtributosCalle"
