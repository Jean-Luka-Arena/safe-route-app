from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.db.models import Usuario
from app.dependencias import obtener_usuario_actual
from app.schemas import IncidenteCrear
from app.services.incidentes_service import (
    reportar_incidente,
    borrar_incidente,
    listar_incidentes_de_usuario,
    ConexionInexistente,
    IncidenteInexistente,
    NoAutorizado,
)

router = APIRouter()


def _serializar(incidente):
    return {
        "id": incidente.id,
        "conexion_id": incidente.conexion_id,
        "usuario_id": incidente.usuario_id,
        "tipo": incidente.tipo,
        "gravedad": incidente.gravedad,
        "fecha": incidente.fecha,
    }


@router.post("/incidents", status_code=201)
def reportar_incidente_endpoint(
    datos: IncidenteCrear,
    sesion: Session = Depends(obtener_sesion),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        incidente = reportar_incidente(
            sesion, datos.conexion_id, usuario.id, datos.tipo, datos.fecha
        )
    except ConexionInexistente as error:
        raise HTTPException(status_code=404, detail=str(error))

    return _serializar(incidente)


@router.get("/incidents/mine")
def listar_mis_incidentes_endpoint(
    sesion: Session = Depends(obtener_sesion),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    incidentes = listar_incidentes_de_usuario(sesion, usuario.id)
    return [_serializar(i) for i in incidentes]


@router.delete("/incidents/{incidente_id}", status_code=204)
def borrar_incidente_endpoint(
    incidente_id: int,
    sesion: Session = Depends(obtener_sesion),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    try:
        borrar_incidente(sesion, incidente_id, usuario.id)
    except IncidenteInexistente as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NoAutorizado:
        raise HTTPException(
            status_code=403, detail="no podés borrar un reporte que no es tuyo"
        )
