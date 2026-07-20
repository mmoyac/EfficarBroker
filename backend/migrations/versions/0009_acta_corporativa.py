"""Acta corporativa: catalogos (comuna/tipo_vehiculo/combustible/tipo_comision)
y campos nuevos en clientes/vehiculos/users/tenants.

Revision ID: 0009_acta_corporativa
Revises: 0008_vehiculo_sucursal_venta
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_acta_corporativa"
down_revision: Union[str, None] = "0008_vehiculo_sucursal_venta"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    # --- Catalogos nuevos ---
    op.create_table(
        "comunas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False, unique=True),
        *_timestamps(),
    )
    op.create_table(
        "tipos_vehiculo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "combustibles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "tipos_comision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("tasa", sa.Numeric(5, 4), nullable=False),
        sa.Column("minimo", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )

    # --- clientes: domicilio + comuna ---
    op.add_column("clientes", sa.Column("domicilio", sa.String(255), nullable=True))
    op.add_column("clientes", sa.Column("comuna_id", sa.Integer(), sa.ForeignKey("comunas.id", ondelete="RESTRICT"), nullable=True))
    op.create_index("ix_clientes_comuna_id", "clientes", ["comuna_id"])

    # --- vehiculos: color + tipo_vehiculo + combustible + tipo_comision ---
    op.add_column("vehiculos", sa.Column("color", sa.String(40), nullable=True))
    op.add_column("vehiculos", sa.Column("tipo_vehiculo_id", sa.Integer(), sa.ForeignKey("tipos_vehiculo.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("vehiculos", sa.Column("combustible_id", sa.Integer(), sa.ForeignKey("combustibles.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("vehiculos", sa.Column("tipo_comision_id", sa.Integer(), sa.ForeignKey("tipos_comision.id", ondelete="RESTRICT"), nullable=True))
    op.create_index("ix_vehiculos_tipo_vehiculo_id", "vehiculos", ["tipo_vehiculo_id"])
    op.create_index("ix_vehiculos_combustible_id", "vehiculos", ["combustible_id"])
    op.create_index("ix_vehiculos_tipo_comision_id", "vehiculos", ["tipo_comision_id"])

    # --- users: rut ---
    op.add_column("users", sa.Column("rut", sa.String(20), nullable=True))

    # --- tenants: datos corporativos ---
    op.add_column("tenants", sa.Column("razon_social", sa.String(150), nullable=True))
    op.add_column("tenants", sa.Column("rut", sa.String(20), nullable=True))
    op.add_column("tenants", sa.Column("giro", sa.String(150), nullable=True))
    op.add_column("tenants", sa.Column("telefono", sa.String(30), nullable=True))
    op.add_column("tenants", sa.Column("web", sa.String(150), nullable=True))
    op.add_column("tenants", sa.Column("logo", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "logo")
    op.drop_column("tenants", "web")
    op.drop_column("tenants", "telefono")
    op.drop_column("tenants", "giro")
    op.drop_column("tenants", "rut")
    op.drop_column("tenants", "razon_social")

    op.drop_column("users", "rut")

    op.drop_index("ix_vehiculos_tipo_comision_id", table_name="vehiculos")
    op.drop_index("ix_vehiculos_combustible_id", table_name="vehiculos")
    op.drop_index("ix_vehiculos_tipo_vehiculo_id", table_name="vehiculos")
    op.drop_column("vehiculos", "tipo_comision_id")
    op.drop_column("vehiculos", "combustible_id")
    op.drop_column("vehiculos", "tipo_vehiculo_id")
    op.drop_column("vehiculos", "color")

    op.drop_index("ix_clientes_comuna_id", table_name="clientes")
    op.drop_column("clientes", "comuna_id")
    op.drop_column("clientes", "domicilio")

    op.drop_table("tipos_comision")
    op.drop_table("combustibles")
    op.drop_table("tipos_vehiculo")
    op.drop_table("comunas")
