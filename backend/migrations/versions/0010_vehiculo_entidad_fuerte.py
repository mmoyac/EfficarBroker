"""Vehiculo como entidad fuerte: separa la ficha del auto del acta de recepcion.

Hasta 0009 la tabla `vehiculos` confundia cuatro conceptos en una fila (el auto,
su dueno, el acta de corretaje y la venta), y el unique (tenant_id, ppu) hacia
imposible recepcionar dos veces el mismo auto.

Esta migracion divide cada fila de `vehiculos` en:
  - `vehiculos`        : identidad fisica del auto (larga vida, N actas)
  - `actas_recepcion`  : el evento de corretaje (dueno, estado, orden de venta, venta)

El id del vehiculo se PRESERVA como id del acta (relacion 1:1 al momento del
corte), lo que permite re-apuntar checklist e historial con un UPDATE directo
sin tabla de mapeo.

Revision ID: 0010_vehiculo_entidad_fuerte
Revises: 0009_acta_corporativa
Create Date: 2026-07-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_vehiculo_entidad_fuerte"
down_revision: Union[str, None] = "0009_acta_corporativa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _catalogo(nombre: str, code_len: int = 40) -> None:
    op.create_table(
        nombre,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(code_len), nullable=False, unique=True),
        sa.Column("nombre", sa.String(80), nullable=False),
        *_timestamps(),
    )


def _seed(tabla: str, filas: list[tuple[str, str]]) -> None:
    conn = op.get_bind()
    for code, nombre in filas:
        conn.execute(
            sa.text(f"INSERT INTO {tabla} (code, nombre) VALUES (:c, :n) ON CONFLICT (code) DO NOTHING"),
            {"c": code, "n": nombre},
        )


def upgrade() -> None:
    conn = op.get_bind()

    # Guard: la migracion vuelve version_id obligatoria. Si hay vehiculos sin
    # version no podemos derivar marca/modelo y perderiamos datos en silencio.
    huerfanos = conn.execute(sa.text("SELECT count(*) FROM vehiculos WHERE version_id IS NULL")).scalar()
    if huerfanos:
        raise RuntimeError(
            f"{huerfanos} vehiculo(s) sin version_id. Asignar version antes de migrar: "
            "marca y modelo pasan a derivarse del catalogo."
        )

    # ------------------------------------------------------------------
    # 1. Catalogos nuevos
    # ------------------------------------------------------------------
    _catalogo("colores")
    _catalogo("estados_abono")
    _catalogo("motivos_cierre_acta")
    _catalogo("tipos_checklist_item")
    _catalogo("estados_checklist")

    _seed("estados_abono", [
        ("NO_DEVENGADO", "Cobrado, no devengado"),
        ("APLICADO_COMISION", "Aplicado a la comision"),
        ("RETENIDO", "Retenido por gestion"),
    ])
    _seed("motivos_cierre_acta", [
        ("DESISTIMIENTO", "El dueno desiste de vender"),
        ("VENTA_EXTERNA", "Vendido por fuera del corredor"),
    ])
    _seed("tipos_checklist_item", [("DOCUMENTO", "Documento"), ("ACCESORIO", "Accesorio")])
    _seed("estados_checklist", [("OK", "OK"), ("FALTANTE", "Faltante"), ("OBSERVADO", "Observado")])

    # Colores a partir de los valores de texto ya cargados.
    conn.execute(sa.text("""
        INSERT INTO colores (code, nombre)
        SELECT DISTINCT UPPER(TRIM(color)), INITCAP(TRIM(color))
        FROM vehiculos
        WHERE color IS NOT NULL AND TRIM(color) <> ''
        ON CONFLICT (code) DO NOTHING
    """))

    # ------------------------------------------------------------------
    # 2. checklist_items.tipo (string libre) -> tipo_id (FK a catalogo)
    # ------------------------------------------------------------------
    op.add_column("checklist_items", sa.Column("tipo_id", sa.Integer(), nullable=True))
    conn.execute(sa.text("""
        UPDATE checklist_items ci
        SET tipo_id = t.id
        FROM tipos_checklist_item t
        WHERE t.code = UPPER(TRIM(ci.tipo))
    """))
    # Cualquier valor no reconocido cae a DOCUMENTO antes de exigir NOT NULL.
    conn.execute(sa.text("""
        UPDATE checklist_items
        SET tipo_id = (SELECT id FROM tipos_checklist_item WHERE code = 'DOCUMENTO')
        WHERE tipo_id IS NULL
    """))
    op.alter_column("checklist_items", "tipo_id", nullable=False)
    op.create_foreign_key(
        "fk_checklist_items_tipo", "checklist_items", "tipos_checklist_item",
        ["tipo_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_index("ix_checklist_items_tipo_id", "checklist_items", ["tipo_id"])
    op.drop_column("checklist_items", "tipo")

    # ------------------------------------------------------------------
    # 3. actas_recepcion
    # ------------------------------------------------------------------
    op.create_table(
        "actas_recepcion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vehiculo_id", sa.Integer(), sa.ForeignKey("vehiculos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("captador_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sucursal_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sucursal_venta_id", sa.Integer(), sa.ForeignKey("sucursales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("estado_id", sa.Integer(), sa.ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("km_ingreso", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fecha_recepcion", sa.Date(), nullable=False),
        # Orden de venta
        sa.Column("precio_venta_pactado", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vigencia_dias", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("tipo_comision_id", sa.Integer(), sa.ForeignKey("tipos_comision.id", ondelete="RESTRICT"), nullable=True),
        # Abono de exclusividad
        sa.Column("exclusividad_abono", sa.Integer(), nullable=False, server_default="40000"),
        sa.Column("estado_abono_id", sa.Integer(), sa.ForeignKey("estados_abono.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fecha_cobro_abono", sa.Date(), nullable=True),
        sa.Column("fecha_resolucion_abono", sa.Date(), nullable=True),
        # Venta
        sa.Column("vendedor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("precio_venta_final", sa.Integer(), nullable=True),
        sa.Column("fecha_venta", sa.Date(), nullable=True),
        # Cierre
        sa.Column("cerrada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("motivo_cierre_id", sa.Integer(), sa.ForeignKey("motivos_cierre_acta.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("fecha_cierre", sa.Date(), nullable=True),
        *_timestamps(),
    )
    for col in ("tenant_id", "vehiculo_id", "cliente_id", "captador_user_id", "sucursal_id",
                "sucursal_venta_id", "estado_id", "tipo_comision_id", "estado_abono_id",
                "vendedor_user_id", "motivo_cierre_id", "cerrada"):
        op.create_index(f"ix_actas_recepcion_{col}", "actas_recepcion", [col])

    # Backfill: un acta por vehiculo, PRESERVANDO el id.
    conn.execute(sa.text("""
        INSERT INTO actas_recepcion (
            id, tenant_id, vehiculo_id, cliente_id, captador_user_id,
            sucursal_id, sucursal_venta_id, estado_id, km_ingreso, fecha_recepcion,
            precio_venta_pactado, vigencia_dias, tipo_comision_id,
            exclusividad_abono, estado_abono_id, fecha_cobro_abono, fecha_resolucion_abono,
            vendedor_user_id, precio_venta_final, fecha_venta,
            cerrada, fecha_cierre, created_at, updated_at
        )
        SELECT
            v.id, v.tenant_id, v.id, v.cliente_id, v.captador_user_id,
            v.sucursal_id, v.sucursal_venta_id, v.estado_id, v.km_ingreso, v.fecha_recepcion,
            v.precio_venta_pactado, v.vigencia_dias, v.tipo_comision_id,
            v.exclusividad_abono,
            CASE WHEN ev.code = 'VENDIDO'
                 THEN (SELECT id FROM estados_abono WHERE code = 'APLICADO_COMISION')
                 ELSE (SELECT id FROM estados_abono WHERE code = 'NO_DEVENGADO')
            END,
            v.fecha_recepcion,
            CASE WHEN ev.code = 'VENDIDO' THEN v.fecha_venta ELSE NULL END,
            v.vendedor_user_id, v.precio_venta_final, v.fecha_venta,
            (ev.code = 'VENDIDO'),
            CASE WHEN ev.code = 'VENDIDO' THEN v.fecha_venta ELSE NULL END,
            v.created_at, v.updated_at
        FROM vehiculos v
        JOIN estados_vehiculo ev ON ev.id = v.estado_id
    """))
    # Los ids vinieron explicitos: avanzar la secuencia para los INSERT futuros.
    conn.execute(sa.text(
        "SELECT setval(pg_get_serial_sequence('actas_recepcion','id'), "
        "COALESCE((SELECT MAX(id) FROM actas_recepcion), 1), true)"
    ))

    # ------------------------------------------------------------------
    # 4. Checklist e historial pasan a colgar del acta
    # ------------------------------------------------------------------
    op.create_table(
        "acta_checklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("acta_id", sa.Integer(), sa.ForeignKey("actas_recepcion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checklist_item_id", sa.Integer(), sa.ForeignKey("checklist_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("presente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("estado_checklist_id", sa.Integer(), sa.ForeignKey("estados_checklist.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("observacion", sa.String(255), nullable=True),
    )
    op.create_index("ix_acta_checklist_acta_id", "acta_checklist", ["acta_id"])
    op.create_index("ix_acta_checklist_estado", "acta_checklist", ["estado_checklist_id"])
    # acta_id = vehiculo_id porque el backfill preservo los ids.
    conn.execute(sa.text("""
        INSERT INTO acta_checklist (
            id, acta_id, checklist_item_id, presente, estado_checklist_id,
            fecha_vencimiento, observacion
        )
        SELECT vc.id, vc.vehiculo_id, vc.checklist_item_id, vc.presente,
               ec.id, vc.fecha_vencimiento, vc.observacion
        FROM vehiculo_checklist vc
        LEFT JOIN estados_checklist ec
          ON ec.code = UPPER(TRIM(COALESCE(vc.estado, '')))
    """))
    conn.execute(sa.text(
        "SELECT setval(pg_get_serial_sequence('acta_checklist','id'), "
        "COALESCE((SELECT MAX(id) FROM acta_checklist), 1), true)"
    ))

    op.create_table(
        "acta_estado_historial",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("acta_id", sa.Integer(), sa.ForeignKey("actas_recepcion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado_id", sa.Integer(), sa.ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_acta_estado_historial_acta_id", "acta_estado_historial", ["acta_id"])
    op.create_index("ix_acta_estado_historial_tenant_id", "acta_estado_historial", ["tenant_id"])
    op.create_index("ix_acta_estado_historial_estado_id", "acta_estado_historial", ["estado_id"])
    conn.execute(sa.text("""
        INSERT INTO acta_estado_historial (id, tenant_id, acta_id, estado_id, user_id, timestamp)
        SELECT h.id, h.tenant_id, h.vehiculo_id, h.estado_id, h.user_id, h.timestamp
        FROM vehiculo_estado_historial h
    """))
    conn.execute(sa.text(
        "SELECT setval(pg_get_serial_sequence('acta_estado_historial','id'), "
        "COALESCE((SELECT MAX(id) FROM acta_estado_historial), 1), true)"
    ))

    op.drop_table("vehiculo_checklist")
    op.drop_table("vehiculo_estado_historial")

    # ------------------------------------------------------------------
    # 5. Adelgazar vehiculos a identidad fisica
    # ------------------------------------------------------------------
    op.add_column("vehiculos", sa.Column("color_id", sa.Integer(), nullable=True))
    conn.execute(sa.text("""
        UPDATE vehiculos v
        SET color_id = c.id
        FROM colores c
        WHERE c.code = UPPER(TRIM(v.color))
    """))
    op.create_foreign_key("fk_vehiculos_color", "vehiculos", "colores", ["color_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_vehiculos_color_id", "vehiculos", ["color_id"])

    # version_id pasa a obligatoria: marca y modelo se derivan del catalogo.
    op.alter_column("vehiculos", "version_id", nullable=False)

    for col in ("cliente_id", "captador_user_id", "sucursal_id", "sucursal_venta_id",
                "estado_id", "km_ingreso", "tipo_comision_id",
                "precio_venta_pactado", "vigencia_dias", "exclusividad_abono", "fecha_recepcion",
                "vendedor_user_id", "precio_venta_final", "fecha_venta",
                "marca", "modelo", "color"):
        op.drop_column("vehiculos", col)

    # ------------------------------------------------------------------
    # 6. INVARIANTE: una sola acta activa por vehiculo.
    # Se garantiza en la base y no solo en el router: dos requests concurrentes
    # para la misma PPU dejarian dos actas activas si solo validara la app.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE UNIQUE INDEX uq_acta_activa_por_vehiculo
        ON actas_recepcion (vehiculo_id) WHERE cerrada = false
    """)


def downgrade() -> None:
    conn = op.get_bind()

    op.execute("DROP INDEX IF EXISTS uq_acta_activa_por_vehiculo")

    # Reconstruir las columnas de vehiculos.
    op.add_column("vehiculos", sa.Column("marca", sa.String(60), nullable=True))
    op.add_column("vehiculos", sa.Column("modelo", sa.String(80), nullable=True))
    op.add_column("vehiculos", sa.Column("color", sa.String(40), nullable=True))
    op.add_column("vehiculos", sa.Column("cliente_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("captador_user_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("sucursal_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("sucursal_venta_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("estado_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("km_ingreso", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("tipo_comision_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("precio_venta_pactado", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("vigencia_dias", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("exclusividad_abono", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("fecha_recepcion", sa.Date(), nullable=True))
    op.add_column("vehiculos", sa.Column("vendedor_user_id", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("precio_venta_final", sa.Integer(), nullable=True))
    op.add_column("vehiculos", sa.Column("fecha_venta", sa.Date(), nullable=True))

    # Marca/modelo desde el catalogo; color desde su FK.
    conn.execute(sa.text("""
        UPDATE vehiculos v
        SET marca = ma.nombre, modelo = mo.nombre
        FROM vehiculo_versiones ve
        JOIN vehiculo_modelos mo ON mo.id = ve.modelo_id
        JOIN vehiculo_marcas ma ON ma.id = mo.marca_id
        WHERE ve.id = v.version_id
    """))
    conn.execute(sa.text("UPDATE vehiculos v SET color = c.nombre FROM colores c WHERE c.id = v.color_id"))

    # Datos operativos desde el acta ACTIVA; si no hay, la mas reciente.
    # OJO: las actas historicas se pierden al revertir. Es aceptable solo
    # mientras no existan reingresos reales (al momento del corte no los hay).
    conn.execute(sa.text("""
        UPDATE vehiculos v SET
            cliente_id = a.cliente_id,
            captador_user_id = a.captador_user_id,
            sucursal_id = a.sucursal_id,
            sucursal_venta_id = a.sucursal_venta_id,
            estado_id = a.estado_id,
            km_ingreso = a.km_ingreso,
            tipo_comision_id = a.tipo_comision_id,
            precio_venta_pactado = a.precio_venta_pactado,
            vigencia_dias = a.vigencia_dias,
            exclusividad_abono = a.exclusividad_abono,
            fecha_recepcion = a.fecha_recepcion,
            vendedor_user_id = a.vendedor_user_id,
            precio_venta_final = a.precio_venta_final,
            fecha_venta = a.fecha_venta
        FROM (
            SELECT DISTINCT ON (vehiculo_id) *
            FROM actas_recepcion
            ORDER BY vehiculo_id, cerrada ASC, fecha_recepcion DESC, id DESC
        ) a
        WHERE a.vehiculo_id = v.id
    """))

    op.create_foreign_key("vehiculos_cliente_id_fkey", "vehiculos", "clientes", ["cliente_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("vehiculos_captador_user_id_fkey", "vehiculos", "users", ["captador_user_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("vehiculos_sucursal_id_fkey", "vehiculos", "sucursales", ["sucursal_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("vehiculos_sucursal_venta_id_fkey", "vehiculos", "sucursales", ["sucursal_venta_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("vehiculos_estado_id_fkey", "vehiculos", "estados_vehiculo", ["estado_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("vehiculos_tipo_comision_id_fkey", "vehiculos", "tipos_comision", ["tipo_comision_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("vehiculos_vendedor_user_id_fkey", "vehiculos", "users", ["vendedor_user_id"], ["id"], ondelete="SET NULL")

    # Restaurar los indices que las migraciones 0009/0008 esperan borrar en su
    # propio downgrade (sus columnas fueron eliminadas por el upgrade de 0010).
    op.create_index("ix_vehiculos_tipo_comision_id", "vehiculos", ["tipo_comision_id"])
    op.create_index("ix_vehiculos_sucursal_venta_id", "vehiculos", ["sucursal_venta_id"])
    op.create_index("ix_vehiculos_vendedor_user_id", "vehiculos", ["vendedor_user_id"])

    op.drop_index("ix_vehiculos_color_id", table_name="vehiculos")
    op.drop_constraint("fk_vehiculos_color", "vehiculos", type_="foreignkey")
    op.drop_column("vehiculos", "color_id")
    op.alter_column("vehiculos", "version_id", nullable=True)

    # Restaurar checklist e historial colgando del vehiculo.
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
    conn.execute(sa.text("""
        INSERT INTO vehiculo_checklist (id, vehiculo_id, checklist_item_id, presente, estado, fecha_vencimiento, observacion)
        SELECT ac.id, a.vehiculo_id, ac.checklist_item_id, ac.presente,
               INITCAP(ec.code), ac.fecha_vencimiento, ac.observacion
        FROM acta_checklist ac
        JOIN actas_recepcion a ON a.id = ac.acta_id
        LEFT JOIN estados_checklist ec ON ec.id = ac.estado_checklist_id
    """))

    op.create_table(
        "vehiculo_estado_historial",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vehiculo_id", sa.Integer(), sa.ForeignKey("vehiculos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("estado_id", sa.Integer(), sa.ForeignKey("estados_vehiculo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vehiculo_estado_historial_vehiculo_id", "vehiculo_estado_historial", ["vehiculo_id"])
    conn.execute(sa.text("""
        INSERT INTO vehiculo_estado_historial (id, tenant_id, vehiculo_id, estado_id, user_id, timestamp)
        SELECT h.id, h.tenant_id, a.vehiculo_id, h.estado_id, h.user_id, h.timestamp
        FROM acta_estado_historial h
        JOIN actas_recepcion a ON a.id = h.acta_id
    """))

    op.drop_table("acta_estado_historial")
    op.drop_table("acta_checklist")
    op.drop_table("actas_recepcion")

    # checklist_items.tipo_id -> tipo (string)
    op.add_column("checklist_items", sa.Column("tipo", sa.String(20), nullable=True))
    conn.execute(sa.text("""
        UPDATE checklist_items ci SET tipo = LOWER(t.code)
        FROM tipos_checklist_item t WHERE t.id = ci.tipo_id
    """))
    op.alter_column("checklist_items", "tipo", nullable=False)
    op.drop_index("ix_checklist_items_tipo_id", table_name="checklist_items")
    op.drop_constraint("fk_checklist_items_tipo", "checklist_items", type_="foreignkey")
    op.drop_column("checklist_items", "tipo_id")

    op.drop_table("estados_checklist")
    op.drop_table("tipos_checklist_item")
    op.drop_table("motivos_cierre_acta")
    op.drop_table("estados_abono")
    op.drop_table("colores")
