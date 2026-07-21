from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import SUPERADMIN, get_current_user, get_effective_tenant_id, require_roles
from src.models.catalogs import Role
from src.models.catalogs import (
    Color,
    Combustible,
    Comuna,
    EstadoAbono,
    EstadoChecklist,
    MotivoCierreActa,
    TipoComision,
    TipoVehiculo,
    VehiculoMarca,
    VehiculoModelo,
    VehiculoVersion,
)
from src.models.sucursal import Sucursal
from src.models.user import User
from src.models.vehiculo import ChecklistItem
from src.schemas.catalogs import (
    CombustibleOut,
    ComunaOut,
    RoleOut,
    SucursalOut,
    TipoComisionOut,
    TipoVehiculoOut,
    VehiculoMarcaIn,
    VehiculoMarcaOut,
    VehiculoModeloIn,
    VehiculoModeloOut,
    VehiculoVersionIn,
    VehiculoVersionOut,
)
from src.schemas.catalogs import CodeNombreOut
from src.schemas.vehiculo import ChecklistItemOut, EquipoVentaOut

router = APIRouter(tags=["catalogs"])


@router.get("/colores", response_model=list[CodeNombreOut])
def list_colores(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Color]:
    return list(db.scalars(select(Color).order_by(Color.nombre)).all())


@router.get("/estados-abono", response_model=list[CodeNombreOut])
def list_estados_abono(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[EstadoAbono]:
    return list(db.scalars(select(EstadoAbono).order_by(EstadoAbono.id)).all())


@router.get("/estados-checklist", response_model=list[CodeNombreOut])
def list_estados_checklist(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[EstadoChecklist]:
    return list(db.scalars(select(EstadoChecklist).order_by(EstadoChecklist.id)).all())


@router.get("/motivos-cierre-acta", response_model=list[CodeNombreOut])
def list_motivos_cierre(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[MotivoCierreActa]:
    return list(db.scalars(select(MotivoCierreActa).order_by(MotivoCierreActa.id)).all())


@router.get("/checklist-items", response_model=list[ChecklistItemOut])
def list_checklist_items(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[ChecklistItem]:
    """Los 12 puntos del acta de recepción (catálogo)."""
    return list(db.scalars(select(ChecklistItem).order_by(ChecklistItem.orden)).all())


@router.get("/comunas", response_model=list[ComunaOut])
def list_comunas(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Comuna]:
    return list(db.scalars(select(Comuna).order_by(Comuna.nombre)).all())


@router.get("/tipos-vehiculo", response_model=list[TipoVehiculoOut])
def list_tipos_vehiculo(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[TipoVehiculo]:
    return list(db.scalars(select(TipoVehiculo).order_by(TipoVehiculo.nombre)).all())


@router.get("/combustibles", response_model=list[CombustibleOut])
def list_combustibles(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[Combustible]:
    return list(db.scalars(select(Combustible).order_by(Combustible.nombre)).all())


@router.get("/tipos-comision", response_model=list[TipoComisionOut])
def list_tipos_comision(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[TipoComision]:
    return list(db.scalars(select(TipoComision).order_by(TipoComision.id)).all())


@router.get("/roles", response_model=list[RoleOut])
def list_assignable_roles(
    db: Session = Depends(get_db),
    _=Depends(require_roles("TenantAdmin")),
) -> list[Role]:
    """Roles asignables dentro de un tenant (excluye SuperAdmin, que es de plataforma)."""
    return list(db.scalars(select(Role).where(Role.code != SUPERADMIN).order_by(Role.id)).all())


@router.get("/equipo-ventas", response_model=list[EquipoVentaOut])
def list_equipo_ventas(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    _=Depends(require_roles("Sales", "Management", "TenantAdmin")),
) -> list[User]:
    """Ejecutivos de ventas activos del tenant (para elegir vendedor)."""
    return list(
        db.scalars(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(User.tenant_id == tenant_id, User.activo.is_(True), Role.code == "Sales")
            .order_by(User.nombre)
        ).all()
    )


@router.get("/sucursales", response_model=list[SucursalOut])
def list_sucursales(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    _=Depends(require_roles("Sales", "Management", "TenantAdmin")),
) -> list[Sucursal]:
    """Sucursales del tenant efectivo (necesarias para levantar actas y gestión)."""
    return list(
        db.scalars(
            select(Sucursal).where(Sucursal.tenant_id == tenant_id).order_by(Sucursal.nombre)
        ).all()
    )


@router.get("/vehiculo-marcas", response_model=list[VehiculoMarcaOut])
def list_vehiculo_marcas(
    db: Session = Depends(get_db),
    _=Depends(require_roles("Sales", "Management", "TenantAdmin")),
) -> list[VehiculoMarca]:
    return list(db.scalars(select(VehiculoMarca).order_by(VehiculoMarca.nombre)).all())


@router.post("/vehiculo-marcas", response_model=VehiculoMarcaOut, status_code=status.HTTP_201_CREATED)
def create_vehiculo_marca(
    body: VehiculoMarcaIn,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> VehiculoMarca:
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre de marca requerido")
    exists = db.scalar(select(VehiculoMarca.id).where(func.lower(VehiculoMarca.nombre) == nombre.lower()))
    if exists:
        raise HTTPException(status_code=409, detail="La marca ya existe")
    marca = VehiculoMarca(nombre=nombre)
    db.add(marca)
    db.commit()
    db.refresh(marca)
    return marca


@router.patch("/vehiculo-marcas/{marca_id}", response_model=VehiculoMarcaOut)
def update_vehiculo_marca(
    marca_id: int,
    body: VehiculoMarcaIn,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> VehiculoMarca:
    marca = db.get(VehiculoMarca, marca_id)
    if marca is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre de marca requerido")
    exists = db.scalar(
        select(VehiculoMarca.id)
        .where(func.lower(VehiculoMarca.nombre) == nombre.lower(), VehiculoMarca.id != marca_id)
    )
    if exists:
        raise HTTPException(status_code=409, detail="La marca ya existe")
    marca.nombre = nombre
    db.commit()
    db.refresh(marca)
    return marca


@router.delete("/vehiculo-marcas/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehiculo_marca(
    marca_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> None:
    marca = db.get(VehiculoMarca, marca_id)
    if marca is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    db.delete(marca)
    db.commit()


@router.get("/vehiculo-modelos", response_model=list[VehiculoModeloOut])
def list_vehiculo_modelos(
    marca_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles("Sales", "Management", "TenantAdmin")),
) -> list[VehiculoModelo]:
    return list(
        db.scalars(
            select(VehiculoModelo)
            .where(VehiculoModelo.marca_id == marca_id)
            .order_by(VehiculoModelo.nombre)
        ).all()
    )


@router.post("/vehiculo-modelos", response_model=VehiculoModeloOut, status_code=status.HTTP_201_CREATED)
def create_vehiculo_modelo(
    body: VehiculoModeloIn,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> VehiculoModelo:
    marca = db.get(VehiculoMarca, body.marca_id)
    if marca is None:
        raise HTTPException(status_code=400, detail="Marca inválida")
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre de modelo requerido")
    exists = db.scalar(
        select(VehiculoModelo.id).where(
            VehiculoModelo.marca_id == body.marca_id,
            func.lower(VehiculoModelo.nombre) == nombre.lower(),
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail="El modelo ya existe para la marca")
    modelo = VehiculoModelo(marca_id=body.marca_id, nombre=nombre)
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return modelo


@router.patch("/vehiculo-modelos/{modelo_id}", response_model=VehiculoModeloOut)
def update_vehiculo_modelo(
    modelo_id: int,
    body: VehiculoModeloIn,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> VehiculoModelo:
    modelo = db.get(VehiculoModelo, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    marca = db.get(VehiculoMarca, body.marca_id)
    if marca is None:
        raise HTTPException(status_code=400, detail="Marca inválida")
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre de modelo requerido")
    exists = db.scalar(
        select(VehiculoModelo.id).where(
            VehiculoModelo.marca_id == body.marca_id,
            func.lower(VehiculoModelo.nombre) == nombre.lower(),
            VehiculoModelo.id != modelo_id,
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail="El modelo ya existe para la marca")
    modelo.marca_id = body.marca_id
    modelo.nombre = nombre
    db.commit()
    db.refresh(modelo)
    return modelo


@router.delete("/vehiculo-modelos/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehiculo_modelo(
    modelo_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> None:
    modelo = db.get(VehiculoModelo, modelo_id)
    if modelo is None:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    db.delete(modelo)
    db.commit()


@router.get("/vehiculo-versiones", response_model=list[VehiculoVersionOut])
def list_vehiculo_versiones(
    modelo_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles("Sales", "Management", "TenantAdmin")),
) -> list[VehiculoVersion]:
    return list(
        db.scalars(
            select(VehiculoVersion)
            .where(VehiculoVersion.modelo_id == modelo_id)
            .order_by(VehiculoVersion.nombre)
        ).all()
    )


@router.post("/vehiculo-versiones", response_model=VehiculoVersionOut, status_code=status.HTTP_201_CREATED)
def create_vehiculo_version(
    body: VehiculoVersionIn,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> VehiculoVersion:
    modelo = db.get(VehiculoModelo, body.modelo_id)
    if modelo is None:
        raise HTTPException(status_code=400, detail="Modelo inválido")
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre de versión requerido")
    exists = db.scalar(
        select(VehiculoVersion.id).where(
            VehiculoVersion.modelo_id == body.modelo_id,
            func.lower(VehiculoVersion.nombre) == nombre.lower(),
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail="La versión ya existe para el modelo")
    version = VehiculoVersion(modelo_id=body.modelo_id, nombre=nombre)
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.patch("/vehiculo-versiones/{version_id}", response_model=VehiculoVersionOut)
def update_vehiculo_version(
    version_id: int,
    body: VehiculoVersionIn,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> VehiculoVersion:
    version = db.get(VehiculoVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Versión no encontrada")
    modelo = db.get(VehiculoModelo, body.modelo_id)
    if modelo is None:
        raise HTTPException(status_code=400, detail="Modelo inválido")
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre de versión requerido")
    exists = db.scalar(
        select(VehiculoVersion.id).where(
            VehiculoVersion.modelo_id == body.modelo_id,
            func.lower(VehiculoVersion.nombre) == nombre.lower(),
            VehiculoVersion.id != version_id,
        )
    )
    if exists:
        raise HTTPException(status_code=409, detail="La versión ya existe para el modelo")
    version.modelo_id = body.modelo_id
    version.nombre = nombre
    db.commit()
    db.refresh(version)
    return version


@router.delete("/vehiculo-versiones/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehiculo_version(
    version_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SUPERADMIN)),
) -> None:
    version = db.get(VehiculoVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Versión no encontrada")
    db.delete(version)
    db.commit()
