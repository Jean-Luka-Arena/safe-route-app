from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.services.auth_service import obtener_usuario_desde_token, TokenInvalido

bearer_scheme = HTTPBearer(auto_error=False)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    sesion: Session = Depends(obtener_sesion),
):
    if credenciales is None:
        raise HTTPException(status_code=401, detail="no autenticado")

    try:
        return obtener_usuario_desde_token(sesion, credenciales.credentials)
    except TokenInvalido:
        raise HTTPException(status_code=401, detail="token inválido o expirado")
