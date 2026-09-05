import datetime
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.db.models import Conexion, Incidente
from app.schemas import IncidenteCrear

router = APIRouter()


@router.post("/incidents", status_code=201)
def reportar_incidente(
    datos: IncidenteCrear, sesion: Session = Depends(obtener_sesion)
):
    """Registra un incidente sobre una calle existente"""
    conexion = sesion.get(Conexion, datos.conexion_id)
    if conexion is None:
        raise HTTPException(
            status_code=404,
            detail=f"la calle con id {datos.conexion_id} no existe",
        )

    incidente = Incidente(
        conexion_id=datos.conexion_id,
        tipo=datos.tipo.value,
        gravedad=datos.gravedad,
        fecha=datos.fecha or datetime.datetime.now(timezone.utc),
    )
    sesion.add(incidente)
    sesion.commit()
    sesion.refresh(incidente)

    return {
        "id": incidente.id,
        "conexion_id": incidente.conexion_id,
        "tipo": incidente.tipo,
        "gravedad": incidente.gravedad,
        "fecha": incidente.fecha,
    }
