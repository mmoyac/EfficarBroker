"""Tasacion prospectos (M1): persistencia de captura inicial.

Revision ID: 0006_tasacion_prospectos
Revises: 0005_vehiculo_venta
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_tasacion_prospectos"
down_revision: Union[str, None] = "0005_vehiculo_venta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "tasacion_prospectos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estado_id", sa.Integer(), sa.ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("captador_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ppu", sa.String(10), nullable=False),
        sa.Column("km", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("precio_mercado", sa.Integer(), nullable=False),
        sa.Column("precio_retoma", sa.Integer(), nullable=False),
        sa.Column("precio_publicacion_sugerido", sa.Integer(), nullable=False),
        sa.Column("fuente", sa.String(50), nullable=False),
        sa.Column("observacion", sa.String(255), nullable=True),
        sa.Column("scrape_url", sa.String(255), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_tasacion_prospectos_tenant_id", "tasacion_prospectos", ["tenant_id"])
    op.create_index("ix_tasacion_prospectos_estado_id", "tasacion_prospectos", ["estado_id"])
    op.create_index("ix_tasacion_prospectos_captador_user_id", "tasacion_prospectos", ["captador_user_id"])
    op.create_index("ix_tasacion_prospectos_ppu", "tasacion_prospectos", ["ppu"])


def downgrade() -> None:
    op.drop_table("tasacion_prospectos")
