"""Tablas CATÁLOGO (globales de plataforma).

Todo atributo enumerado del dominio vive aquí, referenciado por FK desde las
tablas maestras/operacionales. Ningún valor de dominio se hardcodea en código.
Estos catálogos son globales (no llevan tenant_id): definen el vocabulario del
sistema compartido por todos los tenants.
"""

from sqlalchemy import ForeignKey, Integer, Numeric, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TimestampMixin


class Comuna(TimestampMixin, Base):
    """Catálogo de comunas de Chile (domicilio del cliente)."""

    __tablename__ = "comunas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class TipoVehiculo(TimestampMixin, Base):
    """Catálogo de tipo de vehículo (Automóvil, SUV, Camioneta, ...)."""

    __tablename__ = "tipos_vehiculo"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class Combustible(TimestampMixin, Base):
    """Catálogo de combustible (Bencina, Diésel, Híbrido, Eléctrico, ...)."""

    __tablename__ = "combustibles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class Color(TimestampMixin, Base):
    """Catálogo de color del vehículo."""

    __tablename__ = "colores"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class EstadoAbono(TimestampMixin, Base):
    """Catálogo del ciclo de vida del abono de exclusividad.

    NO_DEVENGADO: cobrado al firmar, aún no ganado por la empresa.
    APLICADO_COMISION: la venta se concretó y el abono se descontó de la comisión.
    RETENIDO: venta externa o desistimiento; la empresa lo conserva por gestión.
    """

    __tablename__ = "estados_abono"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class MotivoCierreActa(TimestampMixin, Base):
    """Catálogo de motivos de cierre de un acta sin venta gestionada."""

    __tablename__ = "motivos_cierre_acta"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)  # DESISTIMIENTO, VENTA_EXTERNA
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class TipoChecklistItem(TimestampMixin, Base):
    """Catálogo del tipo de punto del checklist (documento / accesorio)."""

    __tablename__ = "tipos_checklist_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)  # DOCUMENTO, ACCESORIO
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class EstadoChecklist(TimestampMixin, Base):
    """Catálogo del estado de un punto del checklist en una recepción."""

    __tablename__ = "estados_checklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)  # OK, FALTANTE, OBSERVADO
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class TipoComisionEjecutivo(TimestampMixin, Base):
    """Catálogo del tipo de comisión que gana el ejecutivo: captación o venta."""

    __tablename__ = "tipos_comision_ejecutivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)  # CAPTACION, VENTA
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class EstadoPagoComision(TimestampMixin, Base):
    """Catálogo del estado de pago de una comisión de ejecutivo."""

    __tablename__ = "estados_pago_comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)  # PENDIENTE, PAGADA
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class OrigenFoto(TimestampMixin, Base):
    """Catálogo del origen de una foto de la galería.

    URL_CLOUD: la URL vive en un cloud externo (WordPress u otro); no es nuestra.
    ARCHIVO: el archivo se subió al storage propio del backend (borrable con la foto).
    """

    __tablename__ = "origenes_foto"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)  # URL_CLOUD, ARCHIVO
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)


class TipoComision(TimestampMixin, Base):
    """Catálogo de tipo de comisión de corretaje (Estándar 5% / Gold 3%).

    `tasa` es la fracción aplicada al precio (0.05 = 5%); `minimo` el piso en CLP.
    Comisión = MAX(precio * tasa, minimo).
    """

    __tablename__ = "tipos_comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    tasa: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # SuperAdmin, TenantAdmin, ...
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)

    menu_items: Mapped[list["MenuItem"]] = relationship(
        secondary="rol_menu_item", back_populates="roles", lazy="selectin"
    )


class Ciudad(TimestampMixin, Base):
    __tablename__ = "ciudades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class EstadoVehiculo(TimestampMixin, Base):
    """Catálogo del ciclo de vida del vehículo. Lo usarán los módulos M1+."""

    __tablename__ = "estados_vehiculo"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # PROSPECTO, RECEPCIONADO, ...
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# Mapeo N:M entre roles y items de menú (qué opciones ve cada rol)
rol_menu_item = Table(
    "rol_menu_item",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("menu_item_id", ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True),
)


class MenuSeccion(TimestampMixin, Base):
    __tablename__ = "menu_secciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(80), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    items: Mapped[list["MenuItem"]] = relationship(
        back_populates="seccion", order_by="MenuItem.orden", lazy="selectin"
    )


class MenuItem(TimestampMixin, Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    seccion_id: Mapped[int] = mapped_column(
        ForeignKey("menu_secciones.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ruta: Mapped[str] = mapped_column(String(160), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    seccion: Mapped["MenuSeccion"] = relationship(back_populates="items")
    roles: Mapped[list["Role"]] = relationship(
        secondary="rol_menu_item", back_populates="menu_items", lazy="selectin"
    )


class VehiculoMarca(TimestampMixin, Base):
    __tablename__ = "vehiculo_marcas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    modelos: Mapped[list["VehiculoModelo"]] = relationship(
        back_populates="marca", order_by="VehiculoModelo.nombre", lazy="selectin"
    )


class VehiculoModelo(TimestampMixin, Base):
    __tablename__ = "vehiculo_modelos"

    id: Mapped[int] = mapped_column(primary_key=True)
    marca_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculo_marcas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    marca: Mapped["VehiculoMarca"] = relationship(back_populates="modelos", lazy="joined")
    versiones: Mapped[list["VehiculoVersion"]] = relationship(
        back_populates="modelo", order_by="VehiculoVersion.nombre", lazy="selectin"
    )


class VehiculoVersion(TimestampMixin, Base):
    __tablename__ = "vehiculo_versiones"

    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculo_modelos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    modelo: Mapped["VehiculoModelo"] = relationship(back_populates="versiones", lazy="joined")
