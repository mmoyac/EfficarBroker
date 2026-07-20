"""Initial core SaaS schema (catálogos, maestras, operacionales) + trigger append-only

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    # ---------- MAESTRA raíz ----------
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("dominio", sa.String(150), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )

    # ---------- CATÁLOGOS (globales) ----------
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        *_timestamps(),
    )
    op.create_table(
        "ciudades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        *_timestamps(),
    )
    op.create_table(
        "estados_vehiculo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_table(
        "menu_secciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("icon", sa.String(80), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seccion_id", sa.Integer(), sa.ForeignKey("menu_secciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("icon", sa.String(80), nullable=True),
        sa.Column("ruta", sa.String(160), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_menu_items_seccion_id", "menu_items", ["seccion_id"])
    op.create_table(
        "rol_menu_item",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("menu_item_id", sa.Integer(), sa.ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True),
    )

    # ---------- MAESTRAS multitenant ----------
    op.create_table(
        "sucursales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("direccion", sa.String(255), nullable=True),
        sa.Column("ciudad_id", sa.Integer(), sa.ForeignKey("ciudades.id", ondelete="RESTRICT"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_sucursales_tenant_id", "sucursales", ["tenant_id"])
    op.create_index("ix_sucursales_ciudad_id", "sucursales", ["ciudad_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sucursal_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        *_timestamps(),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_sucursal_id", "users", ["sucursal_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ---------- OPERACIONAL: auditoría append-only ----------
    op.create_table(
        "logs_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("entidad", sa.String(80), nullable=True),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("estado_anterior", sa.String(80), nullable=True),
        sa.Column("estado_nuevo", sa.String(80), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_logs_auditoria_tenant_id", "logs_auditoria", ["tenant_id"])
    op.create_index("ix_logs_auditoria_user_id", "logs_auditoria", ["user_id"])

    # Trigger append-only: rechaza UPDATE/DELETE sobre logs_auditoria.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION forbid_mutation_logs_auditoria()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'logs_auditoria es append-only: % no permitido', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_logs_auditoria_append_only
        BEFORE UPDATE OR DELETE ON logs_auditoria
        FOR EACH ROW EXECUTE FUNCTION forbid_mutation_logs_auditoria();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_logs_auditoria_append_only ON logs_auditoria;")
    op.execute("DROP FUNCTION IF EXISTS forbid_mutation_logs_auditoria();")
    op.drop_table("logs_auditoria")
    op.drop_table("users")
    op.drop_table("sucursales")
    op.drop_table("rol_menu_item")
    op.drop_table("menu_items")
    op.drop_table("menu_secciones")
    op.drop_table("estados_vehiculo")
    op.drop_table("ciudades")
    op.drop_table("roles")
    op.drop_table("tenants")
