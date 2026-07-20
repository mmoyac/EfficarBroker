"""Tabla MAESTRA: sucursales (multitenant)."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class Sucursal(TenantMixin, TimestampMixin, Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ciudad_id: Mapped[int] = mapped_column(
        ForeignKey("ciudades.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    ciudad: Mapped["Ciudad"] = relationship(lazy="joined")  # noqa: F821
