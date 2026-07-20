"""Registro central de modelos para que Alembic descubra todo el metadata."""

from src.models.audit import LogAuditoria
from src.models.catalogs import (
    Ciudad,
    Combustible,
    Comuna,
    EstadoVehiculo,
    MenuItem,
    MenuSeccion,
    Role,
    TipoComision,
    TipoVehiculo,
    VehiculoMarca,
    VehiculoModelo,
    VehiculoVersion,
    rol_menu_item,
)
from src.models.cliente import Cliente
from src.models.sucursal import Sucursal
from src.models.tasacion import TasacionProspecto
from src.models.tenant import Tenant
from src.models.user import User
from src.models.vehiculo import (
    ChecklistItem,
    Vehiculo,
    VehiculoChecklist,
    VehiculoEstadoHistorial,
)

__all__ = [
    "Role",
    "Ciudad",
    "Comuna",
    "TipoVehiculo",
    "Combustible",
    "TipoComision",
    "EstadoVehiculo",
    "MenuSeccion",
    "MenuItem",
    "VehiculoMarca",
    "VehiculoModelo",
    "VehiculoVersion",
    "rol_menu_item",
    "Tenant",
    "Sucursal",
    "TasacionProspecto",
    "User",
    "LogAuditoria",
    "Cliente",
    "ChecklistItem",
    "Vehiculo",
    "VehiculoChecklist",
    "VehiculoEstadoHistorial",
]
