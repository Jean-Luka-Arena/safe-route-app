from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.rutas import router as rutas_router
from app.incidentes import router as incidentes_router
from app.ubicaciones import router as ubicaciones_router

app = FastAPI(title="Safe Route API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rutas_router)
app.include_router(incidentes_router)
app.include_router(ubicaciones_router)
