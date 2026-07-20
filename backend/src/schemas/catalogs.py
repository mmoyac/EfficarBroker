from pydantic import BaseModel, ConfigDict


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nombre: str
    descripcion: str | None = None


class SucursalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    direccion: str | None = None
    ciudad_id: int


class ComunaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class TipoVehiculoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nombre: str


class CombustibleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nombre: str


class TipoComisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nombre: str
    tasa: float
    minimo: int


class VehiculoMarcaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class VehiculoModeloOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    marca_id: int
    nombre: str


class VehiculoVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    modelo_id: int
    nombre: str


class VehiculoMarcaIn(BaseModel):
    model_config = ConfigDict(strict=True)

    nombre: str


class VehiculoModeloIn(BaseModel):
    model_config = ConfigDict(strict=True)

    marca_id: int
    nombre: str


class VehiculoVersionIn(BaseModel):
    model_config = ConfigDict(strict=True)

    modelo_id: int
    nombre: str
