from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.repositories.ciudad_repository import obtener_ciudad
from app.services.motor_rutas import calcular_ruta, CRITERIOS_VALIDOS
from app.tda_grafo.excepciones import UbicacionInexistente

router = APIRouter()


@router.get("/route")
def calcular_ruta_endpoint(
    origin: str = Query(..., description="Ubicación de origen"),
    destination: str = Query(..., description="Ubicación de destino"),
    criteria: str = Query(..., description=f"Uno de: {', '.join(CRITERIOS_VALIDOS)}"),
    alpha: Optional[float] = Query(
        None, description="Peso de la distancia (solo si criteria=balanceada)"
    ),
    beta: Optional[float] = Query(
        None, description="Peso del riesgo (solo si criteria=balanceada)"
    ),
):

    ciudad = obtener_ciudad()

    try:
        resultado = calcular_ruta(
            ciudad, origin, destination, criterio=criteria, alpha=alpha, beta=beta
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except UbicacionInexistente as error:
        raise HTTPException(status_code=404, detail=str(error))

    if not resultado.existe_camino():
        raise HTTPException(
            status_code=404,
            detail=f"no existe una ruta entre '{origin}' y '{destination}'",
        )

    return resultado.to_dict()
