"""Menú: eliminar el ítem huérfano 'Nueva Acta de Recepción' (veh_acta).

Revision ID: 0016_drop_menu_veh_acta
Revises: 0015_menu_actas_management
Create Date: 2026-07-21

El ítem `veh_acta` -> "Nueva Acta de Recepción" (`/actas/nueva`) venía del menú
original, cuando ese formulario era el punto de entrada del módulo. Tras el
refactor a `veh_actas` ("Actas de Recepción", grilla `/actas` que ya ofrece el
botón "+ Nueva Acta"), el ítem quedó redundante. El seed hace upsert por `code`,
así que agregó las entradas nuevas pero nunca borró la vieja: sigue apareciendo
en el sidebar de Ventas. Esta migración la elimina (y su mapeo a roles).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_drop_menu_veh_acta"
down_revision: Union[str, None] = "0015_menu_actas_management"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    item_id = conn.execute(
        sa.text("SELECT id FROM menu_items WHERE code = 'veh_acta'")
    ).scalar()
    if item_id is None:
        return  # entorno ya limpio; nada que borrar
    conn.execute(
        sa.text("DELETE FROM rol_menu_item WHERE menu_item_id = :iid"), {"iid": item_id}
    )
    conn.execute(sa.text("DELETE FROM menu_items WHERE id = :iid"), {"iid": item_id})


def downgrade() -> None:
    conn = op.get_bind()

    seccion_id = conn.execute(
        sa.text("SELECT id FROM menu_secciones WHERE code = 'veh_gestion'")
    ).scalar()
    if seccion_id is None:
        return  # entorno sin seed base; nada que recrear

    item_id = conn.execute(
        sa.text("SELECT id FROM menu_items WHERE code = 'veh_acta'")
    ).scalar()
    if item_id is None:
        item_id = conn.execute(
            sa.text(
                """
                INSERT INTO menu_items (seccion_id, code, label, icon, ruta, orden)
                VALUES (:sid, 'veh_acta', 'Nueva Acta de Recepción', 'clipboard', '/actas/nueva', 30)
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
