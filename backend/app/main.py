from fastapi import FastAPI

from app.rutas import router

app = FastAPI(title="Safe Route API")
app.include_router(router)
