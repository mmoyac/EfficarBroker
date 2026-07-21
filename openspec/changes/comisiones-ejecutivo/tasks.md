## 1. Modelo y migración

- [x] 1.1 Catálogos `tipos_comision_ejecutivo` (`CAPTACION`, `VENTA`) y `estados_pago_comision` (`PENDIENTE`, `PAGADA`) en `src/models/catalogs.py`
- [x] 1.2 Maestra `ParametrosComision` (por tenant): `pool_pct`, `captacion_pct`, `venta_pct`
- [x] 1.3 Operacional `ComisionEjecutivo`: `acta_id`, `beneficiario_user_id`, `tipo_id`, `monto`, `estado_pago_id`, `pool_pct`, `porcentaje_aplicado`, `fecha_generacion`, `orden_pago_id` (nullable)
- [x] 1.4 Operacional `OrdenPago`: `tenant_id`, `beneficiario_user_id`, `periodo_desde`, `periodo_hasta`, `fecha_pago`, `monto_comisiones`, `monto_base`, `monto_total`
- [x] 1.5 Migración Alembic (posterior a la última de `vehiculo-entidad-fuerte`): catálogos + maestra + `comisiones` + `ordenes_pago`
- [x] 1.6 Seed: catálogos, y un `parametros_comision` por tenant con `20 / 40 / 60`

## 2. Cálculo y generación

- [x] 2.1 `src/services/comision_ejecutivo.py`: dado el acta vendida y los parámetros, devuelve el monto de captación y de venta (redondeo a peso; residuo a la fila de venta)
- [x] 2.2 En `registrar_venta`: generar las dos comisiones (`CAPTACION` al captador, `VENTA` al vendedor) en `PENDIENTE`, congelando monto y porcentajes, dentro de la misma transacción
- [x] 2.3 Guardas: no generar si el acta no tiene tipo de comisión o precio final; usar default seguro si falta `parametros_comision` (y auditar)

## 3. Backend — endpoints

- [x] 3.1 `GET /api/v1/parametros-comision` y `PATCH /api/v1/parametros-comision` (solo `TenantAdmin`), validando `captacion_pct + venta_pct = 100` y auditando
- [x] 3.2 `GET /api/v1/comisiones` con `?mine`, `?desde/?hasta`, `?estado_pago`; `Sales` ve lo suyo, transversales ven todo el tenant; incluye total
- [x] 3.3 `POST /api/v1/ordenes-pago` (`Management`/`TenantAdmin`): agrupa las comisiones `PENDIENTE` del beneficiario en el período, las marca `PAGADA` y asocia a la orden; recibe `fecha_pago` y `monto_base` (mínimo); calcula `monto_comisiones` y `monto_total`; auditoría. No re-incluye comisiones ya pagadas
- [x] 3.4 `GET /api/v1/ordenes-pago` con `?mine` (ejecutivo ve las suyas; transversales todas) y detalle con las comisiones incluidas
- [x] 3.5 Catálogos expuestos: `GET /api/v1/tipos-comision-ejecutivo`, `GET /api/v1/estados-pago-comision`
- [x] 3.6 `GET /api/v1/estado-resultado` (`Management`/`TenantAdmin`/`SuperAdmin`): ventas y monto transado, comisión de empresa, comisiones de ejecutivos, margen de corretaje, abonos retenidos y comprometidos del período

## 4. Backoffice

- [x] 4.1 Servicios y tipos TypeScript de comisiones y parámetros
- [x] 4.2 `/comisiones` (Sales): grilla de mis comisiones (tipo, acta/PPU, vehículo, cliente, monto, estado de pago), total y filtros por fecha/estado; solo lectura
- [x] 4.3 `/liquidaciones/ordenes` (Management): generar orden de pago de un ejecutivo por período (fecha de pago + mínimo), ver las órdenes emitidas con su detalle
- [x] 4.4 `/config/comisiones` (TenantAdmin): formulario de `pool_pct` + split captación/venta, con la advertencia de que rige hacia adelante
- [x] 4.5 `/bi/resultados` (TenantAdmin): estado de resultados del período con tarjetas (ventas, comisión empresa, comisiones ejecutivos, margen, abonos) y selector de fechas
- [x] 4.6 Rutas en `App.tsx`: `/comisiones`, `/config/comisiones`, `/liquidaciones/ordenes`, `/bi/resultados`

## 5. Pruebas

- [x] 5.1 Venta propia: dos comisiones al mismo ejecutivo cuya suma = `comisión_empresa × pool_pct`
- [x] 5.2 Venta derivada: captación al captador, venta al vendedor, montos correctos
- [x] 5.3 Congelamiento: cambiar los parámetros no altera comisiones ya generadas
- [x] 5.4 Cerrar sin venta no genera comisión
- [x] 5.5 `/comisiones?mine` filtra por beneficiario; `?estado_pago=PENDIENTE` filtra bien
- [x] 5.6 Orden de pago: agrupa las pendientes del ejecutivo en el período y las marca `PAGADA`; `monto_total = base + comisiones`; no re-agrupa ya pagadas; `403` a `Sales`
- [x] 5.7 `PATCH /parametros-comision`: split que no suma 100 → `400`; `Sales` → `403`
- [x] 5.8 Aislamiento entre tenants en comisiones y parámetros
