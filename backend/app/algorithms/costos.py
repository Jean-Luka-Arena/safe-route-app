from functools import partial


def costo_distancia(atributos):
    return atributos.distancia


def riesgo(atributos):
    return 10 - atributos.seguridad


def costo_seguridad(atributos):
    return atributos.distancia * riesgo(atributos)


def costo_balanceado(atributos, alpha, beta):
    if not (0 <= alpha <= 1) or not (0 <= beta <= 1):
        raise ValueError("alpha y beta deben estar entre 0 y 1")
    return alpha * atributos.distancia + beta * riesgo(atributos)


def hacer_costo_balanceado(alpha, beta):
    return partial(costo_balanceado, alpha=alpha, beta=beta)
