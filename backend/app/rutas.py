from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.repositories.ciudad_repository import obtener_ciudad
from app.services.motor_rutas import calcular_ruta, CRITERIOS_VALIDOS
from app.tda_grafo.excepciones import UbicacionInexistente

router = APIRouter()


@router.get("/route")
def calcular_ruta_endpoint(
    origin: int = Query(..., description="Id de la ubicación de origen"),
    destination: int = Query(..., description="Id de la ubicación de destino"),
    criteria: str = Query(..., description=f"Uno de: {', '.join(CRITERIOS_VALIDOS)}"),
    alpha: Optional[float] = Query(
        None,
        ge=0,
        le=1,
        description="Peso de la distancia, entre 0 y 1 (solo si criteria=balanceada)",
    ),
    beta: Optional[float] = Query(
        None,
        ge=0,
        le=1,
        description="Peso del riesgo, entre 0 y 1 (solo si criteria=balanceada)",
    ),
    sesion: Session = Depends(obtener_sesion),
):

    ciudad = obtener_ciudad(sesion)

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
