import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UsuarioRegistro(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TipoIncidente(str, Enum):
    ROBO = "robo"
    ZONA_OSCURA = "zona_oscura"
    CALLE_BLOQUEADA = "calle_bloqueada"
    ACCIDENTE = "accidente"


class IncidenteCrear(BaseModel):
    conexion_id: int
    tipo: TipoIncidente
    fecha: Optional[datetime.datetime] = Field(None)
