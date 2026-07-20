from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    email: EmailStr
    password: str = Field(min_length=1)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    refresh_token: str = Field(min_length=1)


class SelectTenantRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    tenant_id: int


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    telefono: str | None = None
    role: str
    role_code: str
    tenant_id: int | None = None
    tenant: str | None = None
    sucursal_id: int | None = None
    # Tenant activo seleccionado por el SuperAdmin (None en vista plataforma o roles normales)
    active_tenant_id: int | None = None
    active_tenant: str | None = None
