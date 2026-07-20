from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.dependencies import SUPERADMIN, get_current_user, get_effective_tenant_id, require_roles
from src.models.catalogs import Role
from src.models.sucursal import Sucursal
from src.models.user import User
from src.schemas.user import UserCreate, UserOut, UserUpdate
from src.services.user_service import ensure_quota_available
from src.utils.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

# Todos los endpoints exigen rol de gestión (TenantAdmin; SuperAdmin pasa por transversalidad)
# y un tenant efectivo (SuperAdmin debe haber seleccionado uno).
_guard = Depends(require_roles("TenantAdmin"))


def _to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        nombre=user.nombre,
        email=user.email,
        telefono=user.telefono,
        role_id=user.role_id,
        role=user.role.nombre,
        role_code=user.role.code,
        sucursal_id=user.sucursal_id,
        sucursal=user.sucursal.nombre if user.sucursal else None,
        activo=user.activo,
    )


def _get_scoped_user(db: Session, user_id: int, tenant_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


def _validate_role(db: Session, role_id: int) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol inválido")
    if role.code == SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede asignar el rol SuperAdmin dentro de un tenant",
        )
    return role


def _validate_sucursal(db: Session, sucursal_id: int | None, tenant_id: int) -> None:
    if sucursal_id is None:
        return
    suc = db.get(Sucursal, sucursal_id)
    if suc is None or suc.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sucursal inválida")


def _email_taken(db: Session, tenant_id: int, email: str, exclude_id: int | None = None) -> bool:
    stmt = select(User.id).where(User.tenant_id == tenant_id, User.email == email)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt) is not None


@router.get("", response_model=list[UserOut], dependencies=[_guard])
def list_users(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> list[UserOut]:
    users = db.scalars(
        select(User).where(User.tenant_id == tenant_id).order_by(User.nombre)
    ).all()
    return [_to_out(u) for u in users]


@router.get("/{user_id}", response_model=UserOut, dependencies=[_guard])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> UserOut:
    return _to_out(_get_scoped_user(db, user_id, tenant_id))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[_guard])
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> UserOut:
    _validate_role(db, body.role_id)
    _validate_sucursal(db, body.sucursal_id, tenant_id)
    if _email_taken(db, tenant_id, body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email en este tenant",
        )
    ensure_quota_available(db, tenant_id)  # el usuario nace activo → consume cupo

    user = User(
        tenant_id=tenant_id,
        role_id=body.role_id,
        sucursal_id=body.sucursal_id,
        nombre=body.nombre,
        email=body.email,
        telefono=body.telefono,
        password_hash=hash_password(settings.SEED_DEFAULT_PASSWORD),
        activo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_out(user)


@router.patch("/{user_id}", response_model=UserOut, dependencies=[_guard])
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> UserOut:
    user = _get_scoped_user(db, user_id, tenant_id)
    data = body.model_dump(exclude_unset=True)

    if "role_id" in data and data["role_id"] is not None:
        _validate_role(db, data["role_id"])
        user.role_id = data["role_id"]
    if "sucursal_id" in data:
        _validate_sucursal(db, data["sucursal_id"], tenant_id)
        user.sucursal_id = data["sucursal_id"]
    if "nombre" in data and data["nombre"] is not None:
        user.nombre = data["nombre"]
    if "telefono" in data:
        user.telefono = data["telefono"]
    if "activo" in data and data["activo"] is not None:
        if data["activo"] is False and user.id == current.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta",
            )
        # Reactivar consume cupo.
        if data["activo"] is True and not user.activo:
            ensure_quota_available(db, tenant_id)
        user.activo = data["activo"]

    db.commit()
    db.refresh(user)
    return _to_out(user)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[_guard])
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> None:
    user = _get_scoped_user(db, user_id, tenant_id)
    user.password_hash = hash_password(settings.SEED_DEFAULT_PASSWORD)
    db.commit()
