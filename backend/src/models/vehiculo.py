"""Tablas del Acta de Recepción (Módulo 2).

- checklist_items: CATÁLOGO de los 12 puntos de documentos/accesorios.
- vehiculos: OPERACIONAL (multitenant); embebe la orden de venta.
- vehiculo_checklist: OPERACIONAL; estado del checklist por vehículo.
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class ChecklistItem(TimestampMixin, Base):
    """Catálogo global de los 12 puntos del acta."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # documento | accesorio
    requiere_vencimiento: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Vehiculo(TenantMixin, TimestampMixin, Base):
    __tablename__ = "vehiculos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "ppu", name="uq_vehiculos_tenant_ppu"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ppu: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    marca: Mapped[str] = mapped_column(String(60), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    version_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehiculo_versiones.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    n_motor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    n_chasis: Mapped[str | None] = mapped_column(String(60), nullable=True)
    km_ingreso: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tipo_vehiculo_id: Mapped[int | None] = mapped_column(
        ForeignKey("tipos_vehiculo.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    combustible_id: Mapped[int | None] = mapped_column(
        ForeignKey("combustibles.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    tipo_comision_id: Mapped[int | None] = mapped_column(
        ForeignKey("tipos_comision.id", ondelete="RESTRICT"), index=True, nullable=True
    )

    estado_id: Mapped[int] = mapped_column(
        ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    captador_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # sucursal_id = sucursal de ORIGEN/CAPTACIÓN (donde se recibe el auto).
    sucursal_id: Mapped[int] = mapped_column(
        ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # sucursal_venta_id = sucursal donde se gestiona/cierra la venta. Si difiere de
    # sucursal_id el auto está DERIVADO y solo lo venden ejecutivos de esa sucursal.
    sucursal_venta_id: Mapped[int] = mapped_column(
        ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    # Orden de venta (embebida en esta etapa)
    precio_venta_pactado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vigencia_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    exclusividad_abono: Mapped[int] = mapped_column(Integer, nullable=False, default=40000)
    fecha_recepcion: Mapped[date] = mapped_column(Date, nullable=False)

    # Venta (se completa al vender; base para comisión cruzada)
    vendedor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    precio_venta_final: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_venta: Mapped[date | None] = mapped_column(Date, nullable=True)

    estado: Mapped["EstadoVehiculo"] = relationship(lazy="joined")  # noqa: F821
    cliente: Mapped["Cliente"] = relationship(lazy="joined")  # noqa: F821
    captador: Mapped["User"] = relationship(foreign_keys=[captador_user_id], lazy="joined")  # noqa: F821
    vendedor: Mapped["User | None"] = relationship(foreign_keys=[vendedor_user_id], lazy="joined")  # noqa: F821
    sucursal: Mapped["Sucursal"] = relationship(foreign_keys=[sucursal_id], lazy="joined")  # noqa: F821
    sucursal_venta: Mapped["Sucursal"] = relationship(foreign_keys=[sucursal_venta_id], lazy="joined")  # noqa: F821
    version: Mapped["VehiculoVersion | None"] = relationship(lazy="joined")  # noqa: F821
    tipo_vehiculo: Mapped["TipoVehiculo | None"] = relationship(lazy="joined")  # noqa: F821
    combustible: Mapped["Combustible | None"] = relationship(lazy="joined")  # noqa: F821
    tipo_comision: Mapped["TipoComision | None"] = relationship(lazy="joined")  # noqa: F821
    checklist: Mapped[list["VehiculoChecklist"]] = relationship(
        back_populates="vehiculo", cascade="all, delete-orphan", lazy="selectin"
    )


class VehiculoChecklist(Base):
    __tablename__ = "vehiculo_checklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    checklist_item_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_items.id", ondelete="RESTRICT"), nullable=False
    )
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estado: Mapped[str | None] = mapped_column(String(40), nullable=True)  # OK | Faltante | Observado
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    vehiculo: Mapped["Vehiculo"] = relationship(back_populates="checklist")
    item: Mapped["ChecklistItem"] = relationship(lazy="joined")


class VehiculoEstadoHistorial(TenantMixin, Base):
    """Historial de transiciones de estado del vehículo (fuente para KPIs temporales).

    Cada cambio de estado registra el momento exacto y quién lo hizo. Permite
    calcular duración en cada estado y tiempos punta a punta (captación→venta).
    """

    __tablename__ = "vehiculo_estado_historial"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    estado_id: Mapped[int] = mapped_column(
        ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    estado: Mapped["EstadoVehiculo"] = relationship(lazy="joined")  # noqa: F821
