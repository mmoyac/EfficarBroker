from pydantic import BaseModel, ConfigDict, Field


class FotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    acta_id: int
    url: str
    orden: int
    es_principal: bool
    origen: str  # code del catálogo (URL_CLOUD / ARCHIVO)


class FotoUrlIn(BaseModel):
    """Alta de foto por URL ya existente en el cloud."""

    model_config = ConfigDict(strict=True)

    url: str = Field(min_length=1, max_length=500)


class FotoUpdateIn(BaseModel):
    """Reordenar y/o marcar principal. Ambos opcionales."""

    model_config = ConfigDict(strict=True)

    orden: int | None = Field(default=None, ge=0)
    es_principal: bool | None = None


class VideoIn(BaseModel):
    """Enlace de video 360. `null`/vacío borra el video del acta."""

    model_config = ConfigDict(strict=True)

    video_youtube_url: str | None = Field(default=None, max_length=255)
