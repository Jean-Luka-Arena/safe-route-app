import pytest
from app.tda_grafo.atributos_calle import AtributosCalle
from app.algorithms.costos import (
    costo_distancia,
    riesgo,
    costo_seguridad,
    costo_balanceado,
    hacer_costo_balanceado,
)

# ---------- costo_distancia ----------


def test_costo_distancia_devuelve_la_distancia():
    a = AtributosCalle(distancia=500, seguridad=8)
    assert costo_distancia(a) == 500


def test_costo_distancia_ignora_la_seguridad():
    inseguro = AtributosCalle(distancia=500, seguridad=0)
    seguro = AtributosCalle(distancia=500, seguridad=10)
    assert costo_distancia(inseguro) == costo_distancia(seguro)


# ---------- riesgo ----------


def test_riesgo_maximo_con_seguridad_cero():
    a = AtributosCalle(distancia=100, seguridad=0)
    assert riesgo(a) == 10


def test_riesgo_nulo_con_seguridad_maxima():
    a = AtributosCalle(distancia=100, seguridad=10)
    assert riesgo(a) == 0


def test_riesgo_intermedio():
    a = AtributosCalle(distancia=100, seguridad=3)
    assert riesgo(a) == 7


# ---------- costo_seguridad ----------


def test_costo_seguridad_es_distancia_por_riesgo():
    a = AtributosCalle(distancia=100, seguridad=6)
    assert costo_seguridad(a) == 100 * 4


def test_costo_seguridad_nulo_si_es_totalmente_segura():
    a = AtributosCalle(distancia=10_000, seguridad=10)
    assert costo_seguridad(a) == 0


def test_costo_seguridad_penaliza_mas_un_tramo_largo_e_inseguro():
    corto_inseguro = AtributosCalle(distancia=10, seguridad=1)
    largo_inseguro = AtributosCalle(distancia=100, seguridad=1)
    assert costo_seguridad(largo_inseguro) > costo_seguridad(corto_inseguro)


def test_costo_seguridad_penaliza_mas_lo_inseguro_a_igual_distancia():
    seguro = AtributosCalle(distancia=100, seguridad=9)
    inseguro = AtributosCalle(distancia=100, seguridad=1)
    assert costo_seguridad(inseguro) > costo_seguridad(seguro)


# ---------- costo_balanceado ----------


def test_costo_balanceado_alpha_1_beta_0_equivale_a_distancia():
    a = AtributosCalle(distancia=100, seguridad=2)
    assert costo_balanceado(a, alpha=1, beta=0) == costo_distancia(a)


def test_costo_balanceado_alpha_0_beta_1_equivale_a_riesgo_puro():
    a = AtributosCalle(distancia=100, seguridad=2)
    assert costo_balanceado(a, alpha=0, beta=1) == riesgo(a)


def test_costo_balanceado_combina_ambos_criterios():
    a = AtributosCalle(distancia=100, seguridad=4)
    # riesgo = 6
    assert costo_balanceado(a, alpha=0.5, beta=2) == 0.5 * 100 + 2 * 6


def test_costo_balanceado_alpha_negativo_invalido():
    a = AtributosCalle(distancia=100, seguridad=4)
    with pytest.raises(ValueError):
        costo_balanceado(a, alpha=-1, beta=1)


def test_costo_balanceado_beta_negativo_invalido():
    a = AtributosCalle(distancia=100, seguridad=4)
    with pytest.raises(ValueError):
        costo_balanceado(a, alpha=1, beta=-1)


# ---------- hacer_costo_balanceado ----------


def test_hacer_costo_balanceado_devuelve_funcion_de_un_solo_argumento():
    a = AtributosCalle(distancia=100, seguridad=4)
    funcion_costo = hacer_costo_balanceado(alpha=0.5, beta=2)
    assert funcion_costo(a) == costo_balanceado(a, alpha=0.5, beta=2)


def test_distintos_alpha_beta_dan_distintos_costos():
    a = AtributosCalle(distancia=100, seguridad=2)
    prioriza_distancia = hacer_costo_balanceado(alpha=1, beta=0)
    prioriza_seguridad = hacer_costo_balanceado(alpha=0, beta=1)
    assert prioriza_distancia(a) != prioriza_seguridad(a)
