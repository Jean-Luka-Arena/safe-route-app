from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.schemas import UsuarioRegistro, UsuarioLogin, TokenRespuesta
from app.services.auth_service import (
    registrar_usuario,
    autenticar_usuario,
    crear_token_acceso,
    EmailYaRegistrado,
    CredencialesInvalidas,
)

router = APIRouter()


@router.post("/register", status_code=201)
def register(datos: UsuarioRegistro, sesion: Session = Depends(obtener_sesion)):
    try:
        usuario = registrar_usuario(sesion, datos.email, datos.password)
    except EmailYaRegistrado as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {"id": usuario.id, "email": usuario.email}


@router.post("/login", response_model=TokenRespuesta)
def login(datos: UsuarioLogin, sesion: Session = Depends(obtener_sesion)):
    try:
        usuario = autenticar_usuario(sesion, datos.email, datos.password)
    except CredencialesInvalidas:
        raise HTTPException(status_code=401, detail="email o contraseña incorrectos")

    token = crear_token_acceso(usuario)
    return TokenRespuesta(access_token=token)
