"""Galería multimedia del acta: fotos y video 360 de YouTube.

Revision ID: 0014_galeria_multimedia
Revises: 0013_comisiones_ejecutivo
Create Date: 2026-07-21

- Catálogo `origenes_foto` (URL_CLOUD / ARCHIVO).
- Tabla `acta_fotos` (galería de la publicación, cuelga del acta).
- Columna `video_youtube_url` en `actas_recepcion`.
- Índice único parcial: una sola foto principal por acta.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_galeria_multimedia"
down_revision: Union[str, None] = "0013_comisiones_ejecutivo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    # --- Catálogo de orígenes de foto ---
    op.create_table(
        "origenes_foto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        *_timestamps(),
    )
    for code, nombre in [("URL_CLOUD", "URL del cloud"), ("ARCHIVO", "Archivo subido")]:
        conn.execute(
            sa.text("INSERT INTO origenes_foto (code, nombre) VALUES (:c, :n)"),
            {"c": code, "n": nombre},
        )

    # --- Video 360 (YouTube) en el acta ---
    op.add_column(
        "actas_recepcion",
        sa.Column("video_youtube_url", sa.String(255), nullable=True),
    )

    # --- Galería de fotos de la publicación ---
    op.create_table(
        "acta_fotos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("acta_id", sa.Integer(), sa.ForeignKey("actas_recepcion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("origen_id", sa.Integer(), sa.ForeignKey("origenes_foto.id", ondelete="RESTRICT"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_acta_fotos_tenant_id", "acta_fotos", ["tenant_id"])
    op.create_index("ix_acta_fotos_acta_id", "acta_fotos", ["acta_id"])
    op.create_index("ix_acta_fotos_origen_id", "acta_fotos", ["origen_id"])
    # Una sola foto principal por acta (no basta validarlo en el router).
    op.create_index(
        "uq_acta_fotos_principal",
        "acta_fotos",
        ["acta_id"],
        unique=True,
        postgresql_where=sa.text("es_principal"),
    )


def downgrade() -> None:
    op.drop_index("uq_acta_fotos_principal", table_name="acta_fotos")
    op.drop_table("acta_fotos")
    op.drop_column("actas_recepcion", "video_youtube_url")
    op.drop_table("origenes_foto")
