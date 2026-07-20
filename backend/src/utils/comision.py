"""Cálculo de comisión de corretaje y liquidación de pago (derivados).

Comisión = MAX(precio * tasa, minimo). Liquidación = precio - comisión.
No se persisten: se calculan en tiempo de lectura a partir del `tipo_comision`.
"""

from src.models.catalogs import TipoComision


def calcular_comision(precio_venta: int, tipo_comision: TipoComision | None) -> int:
    """Comisión en CLP entero según el tipo. Sin tipo → 0."""
    if tipo_comision is None or precio_venta <= 0:
        return 0
    por_tasa = round(precio_venta * float(tipo_comision.tasa))
    return max(por_tasa, tipo_comision.minimo)


def calcular_liquidacion(precio_venta: int, tipo_comision: TipoComision | None) -> int:
    """Monto a liquidar al cliente = precio - comisión."""
    return precio_venta - calcular_comision(precio_venta, tipo_comision)
