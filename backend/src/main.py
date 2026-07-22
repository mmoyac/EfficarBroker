from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.routers import (
    abonos,
    actas,
    auth,
    catalogs,
    comisiones,
    health,
    multimedia,
    navigation,
    tasacion,
    tenants,
    users,
    vehiculos,
)

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(navigation.router, prefix=settings.API_V1_PREFIX)
app.include_router(tenants.router, prefix=settings.API_V1_PREFIX)
app.include_router(catalogs.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(vehiculos.router, prefix=settings.API_V1_PREFIX)
app.include_router(actas.router, prefix=settings.API_V1_PREFIX)
app.include_router(abonos.router, prefix=settings.API_V1_PREFIX)
app.include_router(comisiones.router, prefix=settings.API_V1_PREFIX)
app.include_router(multimedia.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasacion.router, prefix=settings.API_V1_PREFIX)

# Servir los archivos subidos de la galería (fotos con origen ARCHIVO).
Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL_BASE, StaticFiles(directory=settings.MEDIA_ROOT), name="media")


@app.get("/")
def root() -> dict:
    return {"service": settings.PROJECT_NAME, "docs": "/docs", "api": settings.API_V1_PREFIX}
