from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    nombre: str = Field(min_length=1, max_length=150)
    email: EmailStr
    role_id: int
    sucursal_id: int | None = None
    telefono: str | None = Field(default=None, max_length=30)


class UserUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    telefono: str | None = Field(default=None, max_length=30)
    role_id: int | None = None
    sucursal_id: int | None = None
    activo: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    telefono: str | None = None
    role_id: int
    role: str
    role_code: str
    sucursal_id: int | None = None
    sucursal: str | None = None
    activo: bool
