class UbicacionInexistente(Exception):

    def __init__(self, ubicacion):
        self.ubicacion = ubicacion
        super().__init__(f"la ubicación '{ubicacion}' no existe")
