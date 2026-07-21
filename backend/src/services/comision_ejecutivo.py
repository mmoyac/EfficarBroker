"""Cálculo de la comisión del EJECUTIVO al vender.

La comisión del ejecutivo es una fracción de la comisión de la empresa:
    pool = comisión_empresa × pool_pct/100
y ese pool se reparte entre captación y venta según el split. En venta propia
(captador == vendedor) la misma persona recibe ambas partes.

Redondeo: cada parte se redondea a peso; el residuo (para que capt+venta = pool)
se asigna a la parte de venta, que suele ser la mayor.
"""

from dataclasses import dataclass

from src.models.comision import ParametrosComision
from src.utils.comision import calcular_comision


@dataclass
class RepartoComision:
    comision_empresa: int
    pool: int
    monto_captacion: int
    monto_venta: int
    pool_pct: int
    captacion_pct: int
    venta_pct: int


def calcular_reparto(precio_venta_final: int, tipo_comision, params: ParametrosComision) -> RepartoComision:
    """Calcula el reparto captación/venta de la comisión del ejecutivo."""
    comision_empresa = calcular_comision(precio_venta_final, tipo_comision)
    pool = round(comision_empresa * params.pool_pct / 100)
    monto_captacion = round(pool * params.captacion_pct / 100)
    # El residuo va a venta para que capt + venta == pool exactamente.
    monto_venta = pool - monto_captacion
    return RepartoComision(
        comision_empresa=comision_empresa,
        pool=pool,
        monto_captacion=monto_captacion,
        monto_venta=monto_venta,
        pool_pct=params.pool_pct,
        captacion_pct=params.captacion_pct,
        venta_pct=params.venta_pct,
    )
