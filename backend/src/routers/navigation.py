from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import get_db
from src.dependencies import SUPERADMIN, get_current_user
from src.models.catalogs import MenuItem, MenuSeccion
from src.models.user import User
from src.schemas.navigation import MenuItemOut, MenuSectionOut, NavigationMenuOut

router = APIRouter(prefix="/navigation", tags=["navigation"])


@router.get("/menu", response_model=NavigationMenuOut)
def get_menu(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NavigationMenuOut:
    """Construye el árbol de menú del sidebar desde las tablas catálogo,
    filtrado por el rol del usuario autenticado. Nada hardcodeado."""
    role_code = user.role.code

    secciones = db.scalars(select(MenuSeccion).order_by(MenuSeccion.orden)).all()

    sections_out: list[MenuSectionOut] = []
    for seccion in secciones:
        items_out: list[MenuItemOut] = []
        for item in sorted(seccion.items, key=lambda i: i.orden):
            allowed_codes = {r.code for r in item.roles}
            # SuperAdmin ve todo; el resto ve solo lo mapeado a su rol.
            if role_code == SUPERADMIN or role_code in allowed_codes:
                items_out.append(
                    MenuItemOut(code=item.code, label=item.label, icon=item.icon, ruta=item.ruta)
                )
        if items_out:
            sections_out.append(
                MenuSectionOut(
                    code=seccion.code,
                    label=seccion.label,
                    icon=seccion.icon,
                    items=items_out,
                )
            )
    return NavigationMenuOut(sections=sections_out)
