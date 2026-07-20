"""Catalogos de vehiculo (marca/modelo/version) y FKs operacionales.

Revision ID: 0007_vehiculo_catalogos
Revises: 0006_tasacion_prospectos
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_vehiculo_catalogos"
down_revision: Union[str, None] = "0006_tasacion_prospectos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "vehiculo_marcas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(80), nullable=False, unique=True),
        *_timestamps(),
    )

    op.create_table(
        "vehiculo_modelos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("marca_id", sa.Integer(), sa.ForeignKey("vehiculo_marcas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_vehiculo_modelos_marca_id", "vehiculo_modelos", ["marca_id"])

    op.create_table(
        "vehiculo_versiones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("modelo_id", sa.Integer(), sa.ForeignKey("vehiculo_modelos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_vehiculo_versiones_modelo_id", "vehiculo_versiones", ["modelo_id"])

    op.add_column("vehiculos", sa.Column("version_id", sa.Integer(), sa.ForeignKey("vehiculo_versiones.id", ondelete="RESTRICT"), nullable=True))
    op.create_index("ix_vehiculos_version_id", "vehiculos", ["version_id"])

    op.add_column("tasacion_prospectos", sa.Column("version_id", sa.Integer(), sa.ForeignKey("vehiculo_versiones.id", ondelete="RESTRICT"), nullable=True))
    op.create_index("ix_tasacion_prospectos_version_id", "tasacion_prospectos", ["version_id"])


def downgrade() -> None:
    op.drop_index("ix_tasacion_prospectos_version_id", table_name="tasacion_prospectos")
    op.drop_column("tasacion_prospectos", "version_id")

    op.drop_index("ix_vehiculos_version_id", table_name="vehiculos")
    op.drop_column("vehiculos", "version_id")

    op.drop_table("vehiculo_versiones")
    op.drop_table("vehiculo_modelos")
    op.drop_table("vehiculo_marcas")
