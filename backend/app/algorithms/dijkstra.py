import heapq


def dijkstra(ciudad, origen, destino, funcion_costo):
    """Calcula el camino de costo minimo entre origen y destino en una
    GrafoCiudad, usando el algoritmo de Dijkstra.

    Args:
        ciudad: instancia de GrafoCiudad.
        origen: ubicación de origen.
        destino: ubicación de destino.
        funcion_costo: funcion que recibe un AtributosCalle y devuelve
            un numero >= 0 (el costo de esa calle).

    Returns:
        Una tupla (camino, costo_total):
        - camino: lista de ubicaciones desde origen hasta destino (ambos
          incluidos), en orden. None si no existe camino.
        - costo_total: suma de costos de las calles recorridas.
          float("inf") si no existe camino.

    Complejidad (con heap binario):
        Tiempo: O((V + E) log V), con V = cantidad de ubicaciones y
        E = cantidad de calles.
        Espacio: O(V + E).

    Precondición: funcion_costo debe devolver siempre valores >= 0.
    Dijkstra no da resultados correctos con costos negativos.
    """
    if not ciudad.existe_ubicacion(origen):
        raise Exception(f"la ubicacion '{origen}' no existe")
    if not ciudad.existe_ubicacion(destino):
        raise Exception(f"la ubicacion '{destino}' no existe")

    costos = {origen: 0}
    padres = {origen: None}
    visitados = set()

    heap = [(0, origen)]

    while heap:
        costo_actual, actual = heapq.heappop(heap)

        if actual in visitados:
            continue
        visitados.add(actual)

        if actual == destino:
            break

        for vecino in ciudad.calles_desde(actual):
            if vecino in visitados:
                continue

            atributos = ciudad.obtener_atributos(actual, vecino)
            costo_calle = funcion_costo(atributos)
            nuevo_costo = costo_actual + costo_calle

            if nuevo_costo < costos.get(vecino, float("inf")):
                costos[vecino] = nuevo_costo
                padres[vecino] = actual
                heapq.heappush(heap, (nuevo_costo, vecino))

    if destino not in costos:
        return None, float("inf")

    camino = []
    nodo = destino
    while nodo is not None:
        camino.append(nodo)
        nodo = padres[nodo]
    camino.reverse()

    return camino, costos[destino]
