"""
genera data/seed.json a partir de calles reales de OpenStreetMap (via
Overpass API), para una zona de Buenos Aires.

Uso:
    python scripts/generar_seed_desde_osm.py

requiere la librería `requests` (agregala a tu venv si hace falta:
`pip install requests`).

Nota: este script consulta un servicio publico y gratuito (Overpass
API). Evita correrlo repetidas veces sin necesidad, por respeto a su
política de uso justo.
"""

import json
import math
from pathlib import Path

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

SUR, OESTE, NORTE, ESTE = -34.625, -58.385, -34.600, -58.365

TIPOS_DE_CALLE = "primary|secondary|tertiary|residential|unclassified|living_street"

RUTA_SALIDA = Path(__file__).resolve().parents[1] / "data" / "seed.json"


def consultar_overpass():
    query = f"""
    [out:json][timeout:60];
    (
      way["highway"~"^({TIPOS_DE_CALLE})$"]({SUR},{OESTE},{NORTE},{ESTE});
    );
    out body;
    >;
    out skel qt;
    """
    headers = {"User-Agent": "SafeRoute/1.0 (proyecto educativo, uso personal)"}
    respuesta = requests.post(
        OVERPASS_URL, data={"data": query}, headers=headers, timeout=90
    )
    respuesta.raise_for_status()
    return respuesta.json()


def haversine(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos puntos lat/lon (formula del
    semiverseno)"""
    radio_tierra = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radio_tierra * math.asin(math.sqrt(a))


def calcular_seguridad_inicial(tags):
    seguridad = 6.0

    lit = tags.get("lit")
    if lit == "yes":
        seguridad += 2
    elif lit == "no":
        seguridad -= 2

    if tags.get("highway") in ("primary", "secondary"):
        seguridad += 1

    return max(0.0, min(10.0, seguridad))


def procesar(datos_osm):
    nodos = {}
    ways = []

    for elemento in datos_osm["elements"]:
        if elemento["type"] == "node":
            nodos[elemento["id"]] = (elemento["lat"], elemento["lon"])
        elif elemento["type"] == "way":
            ways.append((elemento["nodes"], elemento.get("tags", {})))

    apariciones = {}
    for ids_de_nodo, _tags in ways:
        for id_nodo in ids_de_nodo:
            apariciones[id_nodo] = apariciones.get(id_nodo, 0) + 1

    intersecciones = set()
    for ids_de_nodo, _tags in ways:
        if not ids_de_nodo:
            continue
        intersecciones.add(ids_de_nodo[0])
        intersecciones.add(ids_de_nodo[-1])
        for id_nodo in ids_de_nodo:
            if apariciones[id_nodo] > 1:
                intersecciones.add(id_nodo)

    conexiones_por_par = {}

    for ids_de_nodo, tags in ways:
        seguridad = calcular_seguridad_inicial(tags)
        distancia_acumulada = 0.0
        origen_actual = ids_de_nodo[0]

        for i in range(1, len(ids_de_nodo)):
            anterior, actual = ids_de_nodo[i - 1], ids_de_nodo[i]
            if anterior not in nodos or actual not in nodos:
                continue

            lat1, lon1 = nodos[anterior]
            lat2, lon2 = nodos[actual]
            distancia_acumulada += haversine(lat1, lon1, lat2, lon2)

            if actual in intersecciones:
                if distancia_acumulada > 0 and origen_actual != actual:
                    clave = (origen_actual, actual)
                    if clave not in conexiones_por_par:
                        conexiones_por_par[clave] = {
                            "origen_id": origen_actual,
                            "destino_id": actual,
                            "distancia": round(distancia_acumulada, 1),
                            "nivel_seguridad": round(seguridad, 1),
                        }
                origen_actual = actual
                distancia_acumulada = 0.0

    ubicaciones = [
        {"id": id_nodo, "latitud": lat, "longitud": lon}
        for id_nodo, (lat, lon) in nodos.items()
        if id_nodo in intersecciones
    ]

    return ubicaciones, list(conexiones_por_par.values())


def main():
    print("Consultando Overpass API (puede tardar unos segundos)...")
    datos_osm = consultar_overpass()

    print("Procesando calles e intersecciones...")
    ubicaciones, conexiones = procesar(datos_osm)

    seed = {"ubicaciones": ubicaciones, "conexiones": conexiones}

    RUTA_SALIDA.parent.mkdir(exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(seed, archivo, ensure_ascii=False, indent=2)

    print(
        f"Listo: {len(ubicaciones)} ubicaciones y {len(conexiones)} "
        f"conexiones guardadas en {RUTA_SALIDA}"
    )


if __name__ == "__main__":
    main()
