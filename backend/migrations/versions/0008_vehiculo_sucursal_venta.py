"""Sucursal de venta del vehiculo (derivacion entre sucursales)

Revision ID: 0008_vehiculo_sucursal_venta
Revises: 0007_vehiculo_catalogos
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_vehiculo_sucursal_venta"
down_revision: Union[str, None] = "0007_vehiculo_catalogos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) columna nullable
    op.add_column(
        "vehiculos",
        sa.Column(
            "sucursal_venta_id",
            sa.Integer(),
            sa.ForeignKey("sucursales.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    # 2) backfill: los autos existentes venden en su propia sucursal de origen
    op.execute("UPDATE vehiculos SET sucursal_venta_id = sucursal_id WHERE sucursal_venta_id IS NULL")
    # 3) imponer NOT NULL + indice
    op.alter_column("vehiculos", "sucursal_venta_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_vehiculos_sucursal_venta_id", "vehiculos", ["sucursal_venta_id"])


def downgrade() -> None:
    op.drop_index("ix_vehiculos_sucursal_venta_id", table_name="vehiculos")
    op.drop_column("vehiculos", "sucursal_venta_id")
