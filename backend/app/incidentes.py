from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.schemas import IncidenteCrear
from app.services.incidentes_service import reportar_incidente, ConexionInexistente

router = APIRouter()


@router.post("/incidents", status_code=201)
def reportar_incidente_endpoint(
    datos: IncidenteCrear, sesion: Session = Depends(obtener_sesion)
):
    try:
        incidente = reportar_incidente(
            sesion, datos.conexion_id, datos.tipo, datos.fecha
        )
    except ConexionInexistente as error:
        raise HTTPException(status_code=404, detail=str(error))

    return {
        "id": incidente.id,
        "conexion_id": incidente.conexion_id,
        "tipo": incidente.tipo,
        "gravedad": incidente.gravedad,
        "fecha": incidente.fecha,
    }
