from app.tda_grafo.grafo_ciudad import GrafoCiudad


def obtener_ciudad():
    """Devuelve la GrafoCiudad que usa la API."""
    ciudad = GrafoCiudad()

    for ubicacion in ["A", "B", "C", "D", "E"]:
        ciudad.agregar_ubicacion(ubicacion)

    ciudad.agregar_calle("A", "B", distancia=500, seguridad=8)
    ciudad.agregar_calle("B", "C", distancia=300, seguridad=4)
    ciudad.agregar_calle("A", "C", distancia=900, seguridad=9)
    ciudad.agregar_calle("C", "D", distancia=400, seguridad=6)
    ciudad.agregar_calle("B", "D", distancia=700, seguridad=9)
    ciudad.agregar_calle("D", "E", distancia=200, seguridad=7)

    return ciudad
