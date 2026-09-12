import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TipoIncidente(str, Enum):
    ROBO = "robo"
    ZONA_OSCURA = "zona_oscura"
    CALLE_BLOQUEADA = "calle_bloqueada"
    ACCIDENTE = "accidente"


class IncidenteCrear(BaseModel):
    conexion_id: int
    tipo: TipoIncidente
    fecha: Optional[datetime.datetime] = Field(
        None, description="Si no se especifica, se usa el momento actual"
    )
