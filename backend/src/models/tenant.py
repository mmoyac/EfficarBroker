"""Tabla MAESTRA raíz: tenants. No lleva tenant_id (es el propio tenant)."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.models.base import TimestampMixin


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    dominio: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Cupo de usuarios licenciado (SaaS): NULL = ilimitado; entero = máximo de usuarios activos.
    max_usuarios: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Datos corporativos para el encabezado/firma del documento (Acta + Orden de Venta).
    razon_social: Mapped[str | None] = mapped_column(String(150), nullable=True)
    rut: Mapped[str | None] = mapped_column(String(20), nullable=True)
    giro: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    web: Mapped[str | None] = mapped_column(String(150), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)  # URL o data URI
