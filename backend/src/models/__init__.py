"""Registro central de modelos para que Alembic descubra todo el metadata."""

from src.models.acta import ActaChecklist, ActaEstadoHistorial, ActaRecepcion
from src.models.audit import LogAuditoria
from src.models.catalogs import (
    Ciudad,
    Color,
    Combustible,
    Comuna,
    EstadoAbono,
    EstadoChecklist,
    EstadoVehiculo,
    MenuItem,
    MenuSeccion,
    MotivoCierreActa,
    Role,
    TipoChecklistItem,
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
from src.models.vehiculo import ChecklistItem, Vehiculo

__all__ = [
    "Role",
    "Ciudad",
    "Comuna",
    "TipoVehiculo",
    "Combustible",
    "Color",
    "TipoComision",
    "EstadoVehiculo",
    "EstadoAbono",
    "MotivoCierreActa",
    "TipoChecklistItem",
    "EstadoChecklist",
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
    "ActaRecepcion",
    "ActaChecklist",
    "ActaEstadoHistorial",
]
