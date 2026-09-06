from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.db.models import Ubicacion

router = APIRouter()


@router.get("/locations")
def listar_ubicaciones(sesion: Session = Depends(obtener_sesion)):
    ubicaciones = sesion.query(Ubicacion).all()
    return [
        {"id": u.id, "latitud": u.latitud, "longitud": u.longitud} for u in ubicaciones
    ]
