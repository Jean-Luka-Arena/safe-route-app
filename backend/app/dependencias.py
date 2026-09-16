from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import obtener_sesion
from app.services.auth_service import obtener_usuario_desde_token, TokenInvalido

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    sesion: Session = Depends(obtener_sesion),
):
    if token is None:
        raise HTTPException(status_code=401, detail="no autenticado")

    try:
        return obtener_usuario_desde_token(sesion, token)
    except TokenInvalido:
        raise HTTPException(status_code=401, detail="token inválido o expirado")
