"""Tablas del ACTA DE RECEPCIÓN (Módulo 2).

El acta es la UNIÓN entre un cliente y un vehículo en un momento dado: todo lo
circunstancial de una consignación (dueño, estado, orden de venta, venta, cierre)
vive acá y no en el vehículo, que es una entidad fuerte de larga vida.

- actas_recepcion: OPERACIONAL (multitenant).
- acta_checklist: OPERACIONAL; checklist de 12 puntos de ESA recepción.
- acta_estado_historial: OPERACIONAL; línea de tiempo de estados de ESA recepción.

INVARIANTE: un vehículo admite N actas históricas pero solo UNA activa. Se
garantiza con un índice único parcial sobre `cerrada = false` creado en la
migración; no basta con validar en el router (dos requests concurrentes).
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class ActaRecepcion(TenantMixin, TimestampMixin, Base):
    __tablename__ = "actas_recepcion"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # Dueño AL MOMENTO de esta recepción (puede ser otro en una recepción futura).
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
    # sucursal_id el acta está DERIVADA y solo la venden ejecutivos de esa sucursal.
    sucursal_venta_id: Mapped[int] = mapped_column(
        ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    estado_id: Mapped[int] = mapped_column(
        ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # Del acta, no del vehículo: el kilometraje varía entre recepciones.
    km_ingreso: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fecha_recepcion: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Orden de venta ---
    precio_venta_pactado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vigencia_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    tipo_comision_id: Mapped[int | None] = mapped_column(
        ForeignKey("tipos_comision.id", ondelete="RESTRICT"), index=True, nullable=True
    )

    # --- Abono de exclusividad ---
    # Anticipo de comisión, NO depósito reembolsable: al vender se descuenta de
    # la comisión (cláusula QUINTA del acta firmada), no se devuelve en efectivo.
    exclusividad_abono: Mapped[int] = mapped_column(Integer, nullable=False, default=40000)
    estado_abono_id: Mapped[int] = mapped_column(
        ForeignKey("estados_abono.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    fecha_cobro_abono: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_resolucion_abono: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Venta ---
    vendedor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    precio_venta_final: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_venta: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Cierre ---
    # `cerrada` es columna y no una consulta sobre estados_vehiculo porque
    # PostgreSQL exige un predicado inmutable en un índice parcial.
    cerrada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    motivo_cierre_id: Mapped[int | None] = mapped_column(
        ForeignKey("motivos_cierre_acta.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    fecha_cierre: Mapped[date | None] = mapped_column(Date, nullable=True)

    vehiculo: Mapped["Vehiculo"] = relationship(back_populates="actas", lazy="joined")  # noqa: F821
    cliente: Mapped["Cliente"] = relationship(lazy="joined")  # noqa: F821
    estado: Mapped["EstadoVehiculo"] = relationship(lazy="joined")  # noqa: F821
    captador: Mapped["User"] = relationship(foreign_keys=[captador_user_id], lazy="joined")  # noqa: F821
    vendedor: Mapped["User | None"] = relationship(foreign_keys=[vendedor_user_id], lazy="joined")  # noqa: F821
    sucursal: Mapped["Sucursal"] = relationship(foreign_keys=[sucursal_id], lazy="joined")  # noqa: F821
    sucursal_venta: Mapped["Sucursal"] = relationship(foreign_keys=[sucursal_venta_id], lazy="joined")  # noqa: F821
    tipo_comision: Mapped["TipoComision | None"] = relationship(lazy="joined")  # noqa: F821
    estado_abono: Mapped["EstadoAbono"] = relationship(lazy="joined")  # noqa: F821
    motivo_cierre: Mapped["MotivoCierreActa | None"] = relationship(lazy="joined")  # noqa: F821
    checklist: Mapped[list["ActaChecklist"]] = relationship(
        back_populates="acta", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def derivado(self) -> bool:
        return self.sucursal_venta_id != self.sucursal_id


class ActaChecklist(Base):
    __tablename__ = "acta_checklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    acta_id: Mapped[int] = mapped_column(
        ForeignKey("actas_recepcion.id", ondelete="CASCADE"), index=True, nullable=False
    )
    checklist_item_id: Mapped[int] = mapped_column(
        ForeignKey("checklist_items.id", ondelete="RESTRICT"), nullable=False
    )
    presente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estado_checklist_id: Mapped[int | None] = mapped_column(
        ForeignKey("estados_checklist.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    acta: Mapped["ActaRecepcion"] = relationship(back_populates="checklist")
    item: Mapped["ChecklistItem"] = relationship(lazy="joined")  # noqa: F821
    estado_checklist: Mapped["EstadoChecklist | None"] = relationship(lazy="joined")  # noqa: F821


class ActaEstadoHistorial(TenantMixin, Base):
    """Historial de transiciones de estado del ACTA (fuente para KPIs temporales).

    Cuelga del acta y no del vehículo: si colgara del vehículo, dos recepciones
    del mismo auto mezclarían sus líneas de tiempo y las duraciones por estado
    quedarían inservibles.
    """

    __tablename__ = "acta_estado_historial"

    id: Mapped[int] = mapped_column(primary_key=True)
    acta_id: Mapped[int] = mapped_column(
        ForeignKey("actas_recepcion.id", ondelete="CASCADE"), index=True, nullable=False
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
