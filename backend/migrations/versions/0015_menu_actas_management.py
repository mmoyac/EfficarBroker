"""Menú: acceso de Management a Actas / Publicación (para gestionar la galería).

Revision ID: 0015_menu_actas_management
Revises: 0014_galeria_multimedia
Create Date: 2026-07-21

La galería multimedia cuelga del acta y se gestiona en `/actas/:id`, pero esa
ruta estaba seedeada solo para `Sales`. Administración/Operaciones (Management)
necesita el enlace para cargar fotos y video de la publicación.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_menu_actas_management"
down_revision: Union[str, None] = "0014_galeria_multimedia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    seccion_id = conn.execute(
        sa.text("SELECT id FROM menu_secciones WHERE code = 'control_valid'")
    ).scalar()
    mgmt_id = conn.execute(
        sa.text("SELECT id FROM roles WHERE code = 'Management'")
    ).scalar()
    if seccion_id is None or mgmt_id is None:
        return  # entorno sin seed base; nada que enlazar

    item_id = conn.execute(
        sa.text("SELECT id FROM menu_items WHERE code = 'val_actas'")
    ).scalar()
    if item_id is None:
        item_id = conn.execute(
            sa.text(
                """
                INSERT INTO menu_items (seccion_id, code, label, icon, ruta, orden)
                VALUES (:sid, 'val_actas', 'Actas / Publicación', 'clipboard-list', '/actas', 15)
                RETURNING id
                """
            ),
            {"sid": seccion_id},
        ).scalar()

    # Mapear el item a Management (idempotente).
    conn.execute(
        sa.text(
            """
            INSERT INTO rol_menu_item (role_id, menu_item_id)
            VALUES (:rid, :iid)
            ON CONFLICT DO NOTHING
            """
        ),
        {"rid": mgmt_id, "iid": item_id},
    )


def downgrade() -> None:
    conn = op.get_bind()
    item_id = conn.execute(
        sa.text("SELECT id FROM menu_items WHERE code = 'val_actas'")
    ).scalar()
    if item_id is not None:
        conn.execute(sa.text("DELETE FROM rol_menu_item WHERE menu_item_id = :iid"), {"iid": item_id})
        conn.execute(sa.text("DELETE FROM menu_items WHERE id = :iid"), {"iid": item_id})
