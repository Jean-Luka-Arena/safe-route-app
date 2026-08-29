import pytest
from app.tda_grafo.grafo_ciudad import GrafoCiudad
from app.services.motor_rutas import calcular_ruta, ResultadoRuta


@pytest.fixture
def ciudad_con_dos_caminos():
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
    return c


# ---------- CRITERIO "corta" ----------


def test_criterio_corta_elige_camino_mas_corto(ciudad_con_dos_caminos):
    resultado = calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="corta")
    assert resultado.camino == ["A", "C", "D"]
    assert resultado.distancia_total == 2


# ---------- CRITERIO "segura" ----------


def test_criterio_segura_elige_camino_mas_seguro(ciudad_con_dos_caminos):
    resultado = calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="segura")
    assert resultado.camino == ["A", "B", "D"]


# ---------- CRITERIO "balanceada" ----------


def test_criterio_balanceada_requiere_alpha_y_beta(ciudad_con_dos_caminos):
    with pytest.raises(ValueError):
        calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="balanceada")


def test_criterio_balanceada_con_alpha_1_beta_0_igual_a_corta(
    ciudad_con_dos_caminos,
):
    balanceada = calcular_ruta(
        ciudad_con_dos_caminos, "A", "D", criterio="balanceada", alpha=1, beta=0
    )
    corta = calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="corta")
    assert balanceada.camino == corta.camino


# ---------- METRICAS DEL RESULTADO ----------


def test_metricas_calculadas_del_camino(ciudad_con_dos_caminos):
    resultado = calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="corta")
    # A-C-D: distancia 1+1=2, seguridad promedio (2+2)/2=2
    assert resultado.distancia_total == 2
    assert resultado.seguridad_promedio == 2


def test_origen_igual_a_destino(ciudad_con_dos_caminos):
    resultado = calcular_ruta(ciudad_con_dos_caminos, "A", "A", criterio="corta")
    assert resultado.camino == ["A"]
    assert resultado.distancia_total == 0


# ---------- SIN CAMINO POSIBLE ----------


def test_sin_camino_posible_devuelve_resultado_vacio(ciudad_desconectada):
    resultado = calcular_ruta(ciudad_desconectada, "A", "C", criterio="corta")
    assert not resultado.existe_camino()
    assert resultado.camino is None
    assert resultado.distancia_total is None


# ---------- CRITERIO INVALIDO ----------


def test_criterio_invalido_lanza_excepcion(ciudad_con_dos_caminos):
    with pytest.raises(ValueError):
        calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="mas_linda")


# ---------- to_dict ----------


def test_to_dict_expone_los_campos_esperados(ciudad_con_dos_caminos):
    resultado = calcular_ruta(ciudad_con_dos_caminos, "A", "D", criterio="corta")
    d = resultado.to_dict()
    assert d["ruta"] == resultado.camino
    assert d["distancia_total"] == resultado.distancia_total
    assert d["seguridad_promedio"] == resultado.seguridad_promedio
    assert d["costo_total"] == resultado.costo_total
