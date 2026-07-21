## Why

La venta ya funciona, pero el ejecutivo no tiene forma de ver lo que gana: la ruta `/comisiones` ("Historial de Incentivos") cae en un placeholder. Y no existe dónde parametrizar cuánto se lleva el equipo de ventas: `/config/comisiones` también es placeholder. Sin esto, la comisión del ejecutivo se calcula a mano y en planilla, sin trazabilidad ni control de pago.

Hoy el sistema solo modela la comisión que la **empresa** le cobra al cliente (`tipos_comision`, Estándar 5% / Gold 3%). Falta modelar la comisión que gana el **ejecutivo**, que es una fracción de esa, repartida entre quien captó el auto y quien cerró la venta.

## What Changes

- **Parámetros de comisión administrables:** nueva maestra `parametros_comision` por tenant (editable por `TenantAdmin` en `/config/comisiones`): `pool_pct` (qué % de la comisión de la empresa se reparte entre los ejecutivos) y el split `captacion_pct` / `venta_pct` (cómo se divide esa parte entre captador y vendedor, deben sumar 100). NO se hardcodean; se siembran con un default (20 / 40 / 60) que el administrador ajusta.
- **Comisión del ejecutivo al vender:** al registrar la venta, el sistema calcula la comisión de la empresa y genera **dos** comisiones de ejecutivo por acta: una de **captación** para el captador y una de **venta** para el vendedor, cada una = `comisión_empresa × pool_pct × (captacion_pct | venta_pct)`. En venta propia (captador = vendedor) la misma persona recibe ambas. El monto y los parámetros usados se **congelan** al momento de la venta: cambiar los porcentajes después no altera las comisiones ya generadas.
- **Estado de pago (liquidación):** cada comisión nace `PENDIENTE` y `Management`/`TenantAdmin` la marca `PAGADA` (individual o en lote), registrando fecha de pago y auditoría.
- **Vista del ejecutivo:** `/comisiones` muestra a cada ejecutivo sus comisiones (como captador y como vendedor) con acta/vehículo/cliente, tipo, monto y estado de pago, con total y filtros por fecha y estado. Solo lectura para el ejecutivo; los roles transversales ven todas las del tenant.
- **Sin venta, sin comisión:** la comisión de ejecutivo se genera solo al vender (requiere comisión de empresa). Cerrar un acta sin venta no genera comisión (el abono de exclusividad es otro concepto, ya modelado en `vehiculo-entidad-fuerte`).

## Capabilities

### New Capabilities
- `comisiones-ejecutivo`: Cálculo, registro, consulta y liquidación de la comisión que gana cada ejecutivo (captación y venta) como fracción parametrizable de la comisión de la empresa.

### Modified Capabilities
<!-- Ninguna delta sobre specs archivadas: capacidad nueva. La generación al vender se implementa en el endpoint de registrar-venta ya existente, pero la regla es nueva. -->

## Impact

- **Depende de:** `vehiculo-entidad-fuerte` (implementado). Usa `actas_recepcion` con `captador_user_id`, `vendedor_user_id`, `tipo_comision_id` y `precio_venta_final`, y `src/utils/comision.py` para la comisión de la empresa.
- **Base de datos:** maestra `parametros_comision` + seed; catálogos `tipos_comision_ejecutivo` (CAPTACION, VENTA) y `estados_pago_comision` (PENDIENTE, PAGADA); operacional `comisiones`.
- **Backend:** `src/services/comision_ejecutivo.py` (cálculo del reparto); `registrar_venta` genera las comisiones; `GET /api/v1/comisiones`, `POST /api/v1/comisiones/{id}/pagar` (y liquidación en lote); CRUD `/api/v1/parametros-comision`.
- **Backoffice:** página `/comisiones` (Sales) y `/config/comisiones` (TenantAdmin); acción de liquidar para Management.
- **Negocio:** el ejecutivo ve su incentivo con trazabilidad; el administrador ajusta los porcentajes sin tocar código; se registra qué está pagado y qué pendiente.
- **Diferido:** bonos por volumen, reglas por tipo de vehículo, y el Estado de Resultados del CEO que consumiría estos montos (se especifican aparte).
