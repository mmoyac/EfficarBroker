"""Tabla MAESTRA: clientes (propietarios de vehículos), multitenant."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class Cliente(TenantMixin, TimestampMixin, Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rut", name="uq_clientes_tenant_rut"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rut: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    domicilio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comuna_id: Mapped[int | None] = mapped_column(
        ForeignKey("comunas.id", ondelete="RESTRICT"), index=True, nullable=True
    )

    comuna: Mapped["Comuna | None"] = relationship(lazy="joined")  # noqa: F821
