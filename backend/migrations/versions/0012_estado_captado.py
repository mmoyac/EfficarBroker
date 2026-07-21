"""Estado CAPTADO: separa la captación (online) de la recepción (auto presente).

Captar es un proceso remoto (WhatsApp/teléfono) donde se recogen datos del
cliente y del vehículo. Recepcionar es cuando el cliente llega con el auto a la
sucursal: recién ahí van checklist, N° motor/chasis, km y fotos, y se firma el
contrato. El acta ahora nace en CAPTADO y pasa a RECEPCIONADO al recepcionar.

Revision ID: 0012_estado_captado
Revises: 0011_acta_observaciones
Create Date: 2026-07-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_estado_captado"
down_revision: Union[str, None] = "0011_acta_observaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Inserta CAPTADO con orden 2 y corre el resto; idempotente.
    conn.execute(sa.text("""
        INSERT INTO estados_vehiculo (code, nombre, orden)
        VALUES ('CAPTADO', 'Captado', 2)
        ON CONFLICT (code) DO NOTHING
    """))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 3 WHERE code = 'RECEPCIONADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 4 WHERE code = 'CONTRATO_ACEPTADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 5 WHERE code = 'PUBLICADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 6 WHERE code = 'VENDIDO'"))


def downgrade() -> None:
    conn = op.get_bind()
    # Reingresa las actas CAPTADAS a RECEPCIONADO antes de quitar el estado.
    recep = conn.execute(sa.text("SELECT id FROM estados_vehiculo WHERE code = 'RECEPCIONADO'")).scalar()
    captado = conn.execute(sa.text("SELECT id FROM estados_vehiculo WHERE code = 'CAPTADO'")).scalar()
    if recep and captado:
        conn.execute(sa.text("UPDATE actas_recepcion SET estado_id = :r WHERE estado_id = :c"),
                     {"r": recep, "c": captado})
        conn.execute(sa.text("UPDATE acta_estado_historial SET estado_id = :r WHERE estado_id = :c"),
                     {"r": recep, "c": captado})
    conn.execute(sa.text("DELETE FROM estados_vehiculo WHERE code = 'CAPTADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 2 WHERE code = 'RECEPCIONADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 3 WHERE code = 'CONTRATO_ACEPTADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 4 WHERE code = 'PUBLICADO'"))
    conn.execute(sa.text("UPDATE estados_vehiculo SET orden = 5 WHERE code = 'VENDIDO'"))
