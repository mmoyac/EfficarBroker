from pydantic import BaseModel, ConfigDict, Field


class TasacionSimularIn(BaseModel):
    model_config = ConfigDict(strict=True)

    ppu: str = Field(min_length=4, max_length=10)
    version_id: int
    anio: int = Field(ge=1900, le=2100)
    km: int = Field(ge=0)
    referencia_url: str | None = Field(default=None, max_length=255)


class TasacionSimularOut(BaseModel):
    prospecto_id: int
    ppu: str
    km: int
    precio_mercado: int
    precio_retoma: int
    precio_publicacion_sugerido: int
    fuente: str
    observacion: str
    sample_size: int = 0
    scrape_url: str | None = None


class TasacionProspectoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ppu: str
    km: int
    precio_mercado: int
    precio_retoma: int
    precio_publicacion_sugerido: int
    fuente: str
    observacion: str | None = None
    sample_size: int
    estado_code: str
    captador: str


class TasacionCatalogOut(BaseModel):
    marcas: list[str]
    modelos: list[str]
    versiones: list[str]
