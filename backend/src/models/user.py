"""Tabla MAESTRA: users.

tenant_id es NULLABLE porque el SuperAdmin de plataforma no pertenece a ningún
tenant. El resto de roles siempre tiene tenant_id.
"""

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Email único por tenant (permite reutilizar el mismo email en otro tenant)
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    sucursal_id: Mapped[int | None] = mapped_column(
        ForeignKey("sucursales.id", ondelete="SET NULL"), index=True, nullable=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # RUT del ejecutivo (aparece en "Firma Ejecutivo" de la Orden de Venta).
    rut: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    role: Mapped["Role"] = relationship(lazy="joined")  # noqa: F821
    tenant: Mapped["Tenant | None"] = relationship(lazy="joined")  # noqa: F821
    sucursal: Mapped["Sucursal | None"] = relationship(lazy="joined")  # noqa: F821
