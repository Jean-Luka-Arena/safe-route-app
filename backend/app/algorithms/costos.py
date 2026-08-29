from functools import partial


def costo_distancia(atributos):
    return atributos.distancia


def riesgo(atributos):
    return 10 - atributos.seguridad


def costo_seguridad(atributos):
    return atributos.distancia * riesgo(atributos)


def costo_balanceado(atributos, alpha, beta):
    if alpha < 0 or beta < 0:
        raise ValueError("alpha y beta deben ser valores no negativos")
    return alpha * atributos.distancia + beta * riesgo(atributos)


def hacer_costo_balanceado(alpha, beta):
    return partial(costo_balanceado, alpha=alpha, beta=beta)
