"""Añade cupo de usuarios (max_usuarios) al tenant

Revision ID: 0002_tenant_quota
Revises: 0001_initial
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_tenant_quota"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NULL = ilimitado; entero = tope de usuarios activos.
    op.add_column("tenants", sa.Column("max_usuarios", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "max_usuarios")
