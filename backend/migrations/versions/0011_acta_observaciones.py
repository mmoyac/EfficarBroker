"""Observaciones de texto libre en el acta de recepción.

El acta real tiene al pie una sección de OBSERVACIONES que el ejecutivo llena a
mano; hasta ahora no había dónde guardarla.

Revision ID: 0011_acta_observaciones
Revises: 0010_vehiculo_entidad_fuerte
Create Date: 2026-07-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_acta_observaciones"
down_revision: Union[str, None] = "0010_vehiculo_entidad_fuerte"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("actas_recepcion", sa.Column("observaciones", sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column("actas_recepcion", "observaciones")
