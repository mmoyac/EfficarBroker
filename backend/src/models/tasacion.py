from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TenantMixin, TimestampMixin


class TasacionProspecto(TenantMixin, TimestampMixin, Base):
    __tablename__ = "tasacion_prospectos"

    id: Mapped[int] = mapped_column(primary_key=True)
    estado_id: Mapped[int] = mapped_column(
        ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    captador_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    version_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehiculo_versiones.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    ppu: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    precio_mercado: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_retoma: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_publicacion_sugerido: Mapped[int] = mapped_column(Integer, nullable=False)

    fuente: Mapped[str] = mapped_column(String(50), nullable=False)
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scrape_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    estado: Mapped["EstadoVehiculo"] = relationship(lazy="joined")  # noqa: F821
    captador: Mapped["User"] = relationship(lazy="joined")  # noqa: F821
    version: Mapped["VehiculoVersion | None"] = relationship(lazy="joined")  # noqa: F821
