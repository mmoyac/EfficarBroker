"""Comisión del ejecutivo, parámetros administrables y liquidación por orden de pago.

Revision ID: 0013_comisiones_ejecutivo
Revises: 0012_estado_captado
Create Date: 2026-07-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_comisiones_ejecutivo"
down_revision: Union[str, None] = "0012_estado_captado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _catalogo(nombre: str) -> None:
    op.create_table(
        nombre,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        *_timestamps(),
    )


def upgrade() -> None:
    conn = op.get_bind()

    _catalogo("tipos_comision_ejecutivo")
    _catalogo("estados_pago_comision")
    for code, nombre in [("CAPTACION", "Captación"), ("VENTA", "Venta")]:
        conn.execute(sa.text("INSERT INTO tipos_comision_ejecutivo (code, nombre) VALUES (:c, :n)"),
                     {"c": code, "n": nombre})
    for code, nombre in [("PENDIENTE", "Pendiente"), ("PAGADA", "Pagada")]:
        conn.execute(sa.text("INSERT INTO estados_pago_comision (code, nombre) VALUES (:c, :n)"),
                     {"c": code, "n": nombre})

    op.create_table(
        "parametros_comision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pool_pct", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("captacion_pct", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("venta_pct", sa.Integer(), nullable=False, server_default="60"),
        *_timestamps(),
    )
    op.create_index("ix_parametros_comision_tenant_id", "parametros_comision", ["tenant_id"])
    # Un registro de parámetros por tenant, sembrado para los existentes.
    conn.execute(sa.text("""
        INSERT INTO parametros_comision (tenant_id, pool_pct, captacion_pct, venta_pct)
        SELECT id, 20, 40, 60 FROM tenants
    """))

    op.create_table(
        "ordenes_pago",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("beneficiario_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("periodo_desde", sa.Date(), nullable=False),
        sa.Column("periodo_hasta", sa.Date(), nullable=False),
        sa.Column("fecha_pago", sa.Date(), nullable=False),
        sa.Column("monto_comisiones", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monto_base", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monto_total", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_ordenes_pago_tenant_id", "ordenes_pago", ["tenant_id"])
    op.create_index("ix_ordenes_pago_beneficiario", "ordenes_pago", ["beneficiario_user_id"])

    op.create_table(
        "comisiones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("acta_id", sa.Integer(), sa.ForeignKey("actas_recepcion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("beneficiario_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo_id", sa.Integer(), sa.ForeignKey("tipos_comision_ejecutivo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("monto", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado_pago_id", sa.Integer(), sa.ForeignKey("estados_pago_comision.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pool_pct", sa.Integer(), nullable=False),
        sa.Column("porcentaje_aplicado", sa.Integer(), nullable=False),
        sa.Column("fecha_generacion", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("orden_pago_id", sa.Integer(), sa.ForeignKey("ordenes_pago.id", ondelete="SET NULL"), nullable=True),
        *_timestamps(),
    )
    for col in ("tenant_id", "acta_id", "beneficiario_user_id", "tipo_id", "estado_pago_id", "orden_pago_id"):
        op.create_index(f"ix_comisiones_{col}", "comisiones", [col])


def downgrade() -> None:
    op.drop_table("comisiones")
    op.drop_table("ordenes_pago")
    op.drop_table("parametros_comision")
    op.drop_table("estados_pago_comision")
    op.drop_table("tipos_comision_ejecutivo")
