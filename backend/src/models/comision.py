"""Comisión del EJECUTIVO (incentivo) y su liquidación.

Distinto de `tipos_comision` (la comisión que la EMPRESA le cobra al cliente).
La comisión del ejecutivo es una fracción de esa, repartida entre captación y
venta, con porcentajes parametrizables por el TenantAdmin.

- parametros_comision: MAESTRA (por tenant); pool + split, editable.
- comisiones: OPERACIONAL; una por beneficiario/tipo al vender. Monto congelado.
- ordenes_pago: OPERACIONAL; agrupa las comisiones de un ejecutivo en un período.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class ParametrosComision(TenantMixin, TimestampMixin, Base):
    """Parámetros de comisión del ejecutivo (un registro por tenant)."""

    __tablename__ = "parametros_comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    # % de la comisión de la empresa que se reparte entre los ejecutivos.
    pool_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    # Split de esa parte entre captador y vendedor (suman 100).
    captacion_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    venta_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=60)


class OrdenPago(TenantMixin, TimestampMixin, Base):
    """Liquidación agrupada: las comisiones de un ejecutivo en un período."""

    __tablename__ = "ordenes_pago"

    id: Mapped[int] = mapped_column(primary_key=True)
    beneficiario_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    periodo_desde: Mapped[date] = mapped_column(Date, nullable=False)
    periodo_hasta: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False)
    monto_comisiones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Mínimo/base del período (lo ingresa el administrador; informativo).
    monto_base: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monto_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    beneficiario: Mapped["User"] = relationship(lazy="joined")  # noqa: F821


class ComisionEjecutivo(TenantMixin, TimestampMixin, Base):
    """Comisión que gana un ejecutivo por un acta vendida (captación o venta).

    El monto y los porcentajes se congelan al generarse: cambiar los parámetros
    o el precio después no la altera.
    """

    __tablename__ = "comisiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    acta_id: Mapped[int] = mapped_column(
        ForeignKey("actas_recepcion.id", ondelete="CASCADE"), index=True, nullable=False
    )
    beneficiario_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_comision_ejecutivo.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    monto: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado_pago_id: Mapped[int] = mapped_column(
        ForeignKey("estados_pago_comision.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # Parámetros usados, congelados para trazabilidad.
    pool_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    porcentaje_aplicado: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    orden_pago_id: Mapped[int | None] = mapped_column(
        ForeignKey("ordenes_pago.id", ondelete="SET NULL"), index=True, nullable=True
    )

    acta: Mapped["ActaRecepcion"] = relationship(lazy="joined")  # noqa: F821
    beneficiario: Mapped["User"] = relationship(lazy="joined")  # noqa: F821
    tipo: Mapped["TipoComisionEjecutivo"] = relationship(lazy="joined")  # noqa: F821
    estado_pago: Mapped["EstadoPagoComision"] = relationship(lazy="joined")  # noqa: F821
    orden_pago: Mapped["OrdenPago | None"] = relationship(lazy="joined")  # noqa: F821
