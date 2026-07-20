"""Acta de recepción: clientes, checklist_items, vehiculos, vehiculo_checklist

Revision ID: 0003_acta_recepcion
Revises: 0002_tenant_quota
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_acta_recepcion"
down_revision: Union[str, None] = "0002_tenant_quota"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    # CATÁLOGO: checklist_items
    op.create_table(
        "checklist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("requiere_vencimiento", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )

    # MAESTRA: clientes
    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rut", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.UniqueConstraint("tenant_id", "rut", name="uq_clientes_tenant_rut"),
        *_timestamps(),
    )
    op.create_index("ix_clientes_tenant_id", "clientes", ["tenant_id"])
    op.create_index("ix_clientes_rut", "clientes", ["rut"])

    # OPERACIONAL: vehiculos (orden de venta embebida)
    op.create_table(
        "vehiculos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ppu", sa.String(10), nullable=False),
        sa.Column("marca", sa.String(60), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("n_motor", sa.String(60), nullable=True),
        sa.Column("n_chasis", sa.String(60), nullable=True),
        sa.Column("km_ingreso", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado_id", sa.Integer(), sa.ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("captador_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sucursal_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("precio_venta_pactado", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vigencia_dias", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("exclusividad_abono", sa.Integer(), nullable=False, server_default="40000"),
        sa.Column("fecha_recepcion", sa.Date(), nullable=False),
        sa.UniqueConstraint("tenant_id", "ppu", name="uq_vehiculos_tenant_ppu"),
        *_timestamps(),
    )
    for col in ("tenant_id", "ppu", "estado_id", "cliente_id", "captador_user_id", "sucursal_id"):
        op.create_index(f"ix_vehiculos_{col}", "vehiculos", [col])

    # OPERACIONAL: vehiculo_checklist
    op.create_table(
        "vehiculo_checklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vehiculo_id", sa.Integer(), sa.ForeignKey("vehiculos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checklist_item_id", sa.Integer(), sa.ForeignKey("checklist_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("presente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("estado", sa.String(40), nullable=True),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("observacion", sa.String(255), nullable=True),
    )
    op.create_index("ix_vehiculo_checklist_vehiculo_id", "vehiculo_checklist", ["vehiculo_id"])


def downgrade() -> None:
    op.drop_table("vehiculo_checklist")
    op.drop_table("vehiculos")
    op.drop_table("clientes")
    op.drop_table("checklist_items")
