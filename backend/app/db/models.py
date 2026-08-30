from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Ubicacion(Base):
    """una ubicacion/interseccion de la ciudad.

    id funciona como identificador de vertice del grafo
    """

    __tablename__ = "ubicaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self):
        return (
            f"Ubicacion(id={self.id}, latitud={self.latitud}, longitud={self.longitud})"
        )


class Conexion(Base):
    """Una calle que conecta dos ubicaciones, con su distancia y nivel
    de seguridad. Es el equivalente persistido de una arista + sus
    AtributosCalle en GrafoCiudad.
    """

    __tablename__ = "conexiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origen_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id"), nullable=False)
    destino_id: Mapped[int] = mapped_column(
        ForeignKey("ubicaciones.id"), nullable=False
    )
    distancia: Mapped[float] = mapped_column(Float, nullable=False)
    nivel_seguridad: Mapped[float] = mapped_column(Float, nullable=False)

    origen: Mapped["Ubicacion"] = relationship(foreign_keys=[origen_id])
    destino: Mapped["Ubicacion"] = relationship(foreign_keys=[destino_id])

    def __repr__(self):
        return (
            f"Conexion(origen_id={self.origen_id}, destino_id={self.destino_id}, "
            f"distancia={self.distancia}, nivel_seguridad={self.nivel_seguridad})"
        )
