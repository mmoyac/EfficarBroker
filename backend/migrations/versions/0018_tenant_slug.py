"""Slug de backoffice del tenant (subdominio efficar-<slug>.effi4tech.cl).

Revision ID: 0018_tenant_slug
Revises: 0017_menu_actas_solo_management
Create Date: 2026-07-22

Columna `slug` (nullable, única) en `tenants`. La usa la identidad PWA host-aware
para resolver el tenant por el dominio del backoffice. Nullable + única: en Postgres
varios NULL conviven; el seed la rellena para el tenant real tras la migración.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_tenant_slug"
down_revision: Union[str, None] = "0017_menu_actas_solo_management"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("slug", sa.String(80), nullable=True))
    op.create_unique_constraint("uq_tenants_slug", "tenants", ["slug"])


def downgrade() -> None:
    op.drop_constraint("uq_tenants_slug", "tenants", type_="unique")
    op.drop_column("tenants", "slug")
