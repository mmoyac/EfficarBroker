"""Menú: 'Actas de Recepción' solo para Management; corregir orden de captaciones.

Revision ID: 0017_menu_actas_solo_management
Revises: 0016_drop_menu_veh_acta
Create Date: 2026-07-21

Para el rol Sales, `veh_actas` ("Actas de Recepción", /actas) mostraba la misma
data que `veh_captaciones` ("Mis Captaciones", /captaciones) pero como grilla de
solo lectura, sin las acciones (recepcionar, vender, PDF, etc.). Era redundante.
La grilla /actas mantiene valor como vista de supervisión de tenant para
Management, que ya la ve vía `val_actas`. Se elimina `veh_actas` (y su mapeo a
Sales).

Además, `veh_captaciones` había quedado con orden=20 (colisionando con el
extinto `veh_actas`) mientras el seed lo define en 30. Se corrige.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_menu_actas_solo_management"
down_revision: Union[str, None] = "0016_drop_menu_veh_acta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Eliminar el ítem redundante veh_actas (y su mapeo a roles).
    item_id = conn.execute(
        sa.text("SELECT id FROM menu_items WHERE code = 'veh_actas'")
    ).scalar()
    if item_id is not None:
        conn.execute(
            sa.text("DELETE FROM rol_menu_item WHERE menu_item_id = :iid"), {"iid": item_id}
        )
        conn.execute(sa.text("DELETE FROM menu_items WHERE id = :iid"), {"iid": item_id})

    # 2) Corregir el orden de veh_captaciones (seed lo define en 30).
    conn.execute(
        sa.text("UPDATE menu_items SET orden = 30 WHERE code = 'veh_captaciones'")
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("UPDATE menu_items SET orden = 20 WHERE code = 'veh_captaciones'")
    )

    seccion_id = conn.execute(
        sa.text("SELECT id FROM menu_secciones WHERE code = 'veh_gestion'")
    ).scalar()
    if seccion_id is None:
        return

    item_id = conn.execute(
        sa.text("SELECT id FROM menu_items WHERE code = 'veh_actas'")
    ).scalar()
    if item_id is None:
        item_id = conn.execute(
            sa.text(
                """
                INSERT INTO menu_items (seccion_id, code, label, icon, ruta, orden)
                VALUES (:sid, 'veh_actas', 'Actas de Recepción', 'clipboard-list', '/actas', 20)
                RETURNING id
                """
            ),
            {"sid": seccion_id},
        ).scalar()

    sales_id = conn.execute(
        sa.text("SELECT id FROM roles WHERE code = 'Sales'")
    ).scalar()
    if sales_id is not None:
        conn.execute(
            sa.text(
                """
                INSERT INTO rol_menu_item (role_id, menu_item_id)
                VALUES (:rid, :iid)
                ON CONFLICT DO NOTHING
                """
            ),
            {"rid": sales_id, "iid": item_id},
        )
