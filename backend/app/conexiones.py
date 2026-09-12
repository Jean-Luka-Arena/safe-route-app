from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.db.models import Conexion

router = APIRouter()


@router.get("/connections")
def listar_conexiones(sesion: Session = Depends(obtener_sesion)):
    conexiones = sesion.query(Conexion).all()
    return [
        {
            "id": c.id,
            "origen_id": c.origen_id,
            "destino_id": c.destino_id,
        }
        for c in conexiones
    ]
