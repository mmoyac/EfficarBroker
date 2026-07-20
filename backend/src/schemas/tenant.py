from pydantic import BaseModel, ConfigDict


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    dominio: str
    activo: bool
    max_usuarios: int | None = None  # NULL = ilimitado
    usuarios_activos: int = 0


class TenantUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    # None explícito = ilimitado. Se usa exclude_unset para distinguir "no enviado".
    max_usuarios: int | None = None
