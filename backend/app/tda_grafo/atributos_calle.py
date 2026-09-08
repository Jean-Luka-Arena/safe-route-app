class AtributosCalle:
    def __init__(self, distancia, seguridad):
        if distancia < 0:
            raise ValueError("la distancia no puede ser negativa")
        if not (0 <= seguridad <= 10):
            raise ValueError("la seguridad debe estar entre 0 y 10")

        self.distancia = distancia
        self.seguridad = seguridad

    def __eq__(self, other):
        if not isinstance(other, AtributosCalle):
            return NotImplemented
        return self.distancia == other.distancia and self.seguridad == other.seguridad

    def __repr__(self):
        return f"AtributosCalle(distancia={self.distancia}, seguridad={self.seguridad})"
