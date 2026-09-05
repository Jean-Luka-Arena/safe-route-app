from fastapi import FastAPI

from app.rutas import router as rutas_router
from app.incidentes import router as incidentes_router

app = FastAPI(title="Safe Route API")
app.include_router(rutas_router)
app.include_router(incidentes_router)
