"""Campos de venta del vehículo (vendedor, precio final, fecha)

Revision ID: 0005_vehiculo_venta
Revises: 0004_estado_historial
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_vehiculo_venta"
down_revision: Union[str, None] = "0004_estado_historial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vehiculos", sa.Column("vendedor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("vehiculos", sa.Column("precio_venta_final", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("fecha_venta", sa.Date(), nullable=True))
    op.create_index("ix_vehiculos_vendedor_user_id", "vehiculos", ["vendedor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_vehiculos_vendedor_user_id", table_name="vehiculos")
    op.drop_column("vehiculos", "fecha_venta")
    op.drop_column("vehiculos", "precio_venta_final")
    op.drop_column("vehiculos", "vendedor_user_id")
