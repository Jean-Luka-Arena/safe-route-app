import json
from pathlib import Path

from app.db.database import SessionLocal
from app.db.models import Ubicacion, Conexion

RUTA_SEED = Path(__file__).resolve().parents[3] / "data" / "seed.json"


def cargar_datos_de_prueba():
    """Carga las ubicaciones y conexiones de data/seed.json en la base.

    No hace nada si ya hay ubicaciones cargadas, para evitar duplicar
    datos si el script se corre mas de una vez.
    """
    sesion = SessionLocal()
    try:
        if sesion.query(Ubicacion).first() is not None:
            print("Ya hay datos cargados, no se vuelve a sembrar.")
            return

        with open(RUTA_SEED, encoding="utf-8") as archivo:
            datos = json.load(archivo)

        for u in datos["ubicaciones"]:
            sesion.add(
                Ubicacion(id=u["id"], latitud=u["latitud"], longitud=u["longitud"])
            )
        sesion.flush()

        for c in datos["conexiones"]:
            sesion.add(
                Conexion(
                    origen_id=c["origen_id"],
                    destino_id=c["destino_id"],
                    distancia=c["distancia"],
                    nivel_seguridad=c["nivel_seguridad"],
                )
            )

        sesion.commit()
        print(
            f"Cargadas {len(datos['ubicaciones'])} ubicaciones "
            f"y {len(datos['conexiones'])} conexiones."
        )
    finally:
        sesion.close()


if __name__ == "__main__":
    cargar_datos_de_prueba()
