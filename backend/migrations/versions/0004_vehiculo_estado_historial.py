"""Historial de estados del vehículo (KPIs temporales)

Revision ID: 0004_estado_historial
Revises: 0003_acta_recepcion
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_estado_historial"
down_revision: Union[str, None] = "0003_acta_recepcion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehiculo_estado_historial",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vehiculo_id", sa.Integer(), sa.ForeignKey("vehiculos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado_id", sa.Integer(), sa.ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_veh_estado_hist_tenant_id", "vehiculo_estado_historial", ["tenant_id"])
    op.create_index("ix_veh_estado_hist_vehiculo_id", "vehiculo_estado_historial", ["vehiculo_id"])
    op.create_index("ix_veh_estado_hist_estado_id", "vehiculo_estado_historial", ["estado_id"])


def downgrade() -> None:
    op.drop_table("vehiculo_estado_historial")
