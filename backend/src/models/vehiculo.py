"""Tablas del vehículo como ENTIDAD FUERTE (Módulo 2).

- checklist_items: CATÁLOGO de los 12 puntos de documentos/accesorios.
- vehiculos: MAESTRA (multitenant); solo la identidad física del auto.

El dueño, el estado, la orden de venta y la venta NO viven acá: son
circunstanciales de cada recepción y pertenecen al acta (ver models/acta.py).
Un mismo vehículo puede recepcionarse y venderse varias veces a lo largo del
tiempo, con dueños distintos.
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class ChecklistItem(TimestampMixin, Base):
    """Catálogo global de los 12 puntos del acta."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_checklist_item.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    requiere_vencimiento: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tipo: Mapped["TipoChecklistItem"] = relationship(lazy="joined")  # noqa: F821


class Vehiculo(TenantMixin, TimestampMixin, Base):
    """ENTIDAD FUERTE: la identidad física del auto.

    Marca y modelo NO se guardan como texto: se derivan de `version_id` a través
    del catálogo vehicular, que es la única fuente de verdad.
    """

    __tablename__ = "vehiculos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ppu", name="uq_vehiculos_tenant_ppu"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ppu: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculo_versiones.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    n_motor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    n_chasis: Mapped[str | None] = mapped_column(String(60), nullable=True)
    color_id: Mapped[int | None] = mapped_column(
        ForeignKey("colores.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    tipo_vehiculo_id: Mapped[int | None] = mapped_column(
        ForeignKey("tipos_vehiculo.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    combustible_id: Mapped[int | None] = mapped_column(
        ForeignKey("combustibles.id", ondelete="RESTRICT"), index=True, nullable=True
    )

    version: Mapped["VehiculoVersion"] = relationship(lazy="joined")  # noqa: F821
    color: Mapped["Color | None"] = relationship(lazy="joined")  # noqa: F821
    tipo_vehiculo: Mapped["TipoVehiculo | None"] = relationship(lazy="joined")  # noqa: F821
    combustible: Mapped["Combustible | None"] = relationship(lazy="joined")  # noqa: F821
    actas: Mapped[list["ActaRecepcion"]] = relationship(  # noqa: F821
        back_populates="vehiculo",
        order_by="desc(ActaRecepcion.fecha_recepcion), desc(ActaRecepcion.id)",
        lazy="selectin",
    )

    @property
    def modelo(self) -> "VehiculoModelo":  # noqa: F821
        return self.version.modelo

    @property
    def marca(self) -> "VehiculoMarca":  # noqa: F821
        return self.version.modelo.marca

    @property
    def marca_nombre(self) -> str:
        return self.version.modelo.marca.nombre

    @property
    def modelo_nombre(self) -> str:
        return self.version.modelo.nombre
