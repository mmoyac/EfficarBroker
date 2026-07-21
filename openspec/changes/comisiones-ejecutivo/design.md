## Context

La comisión de la empresa ya está: `tipos_comision` (Estándar 5% / Gold 3%) y `calcular_comision = MAX(precio × tasa, minimo)` en [src/utils/comision.py](../../../backend/src/utils/comision.py). El acta, tras `registrar-venta`, tiene `captador_user_id`, `vendedor_user_id`, `tipo_comision_id` y `precio_venta_final` — todo lo necesario para derivar la comisión del ejecutivo.

Lo que falta es la capa de **incentivo del ejecutivo**: cuánto de esa comisión de empresa se lleva el equipo de ventas y cómo se reparte entre quien captó y quien vendió. El usuario definió el modelo (% de la comisión de la empresa, repartido captación/venta) pero los porcentajes los fija el `TenantAdmin`, no el código.

El menú ya reserva las rutas: `com_historial` → `/comisiones` (Sales) y `cfg_comision` → `/config/comisiones` (TenantAdmin).

## Goals / Non-Goals

**Goals:**
- Que el ejecutivo vea, con trazabilidad, lo que gana por captación y por venta.
- Que el `TenantAdmin` ajuste los porcentajes sin tocar código.
- Registrar el estado de pago (liquidación) de cada comisión.
- Montos reproducibles y auditables: lo que se muestra es lo que se generó al vender.

**Non-Goals:**
- Bonos por volumen, metas, o reglas por tipo de vehículo.
- El Estado de Resultados del CEO (consumirá estos montos; se especifica aparte).
- Recalcular comisiones históricas al cambiar parámetros o precios.
- Modelar la comisión de la empresa (ya existe) ni el abono de exclusividad (ya modelado).

## Decisions

### 1. Los porcentajes son una maestra, no constantes

`parametros_comision` por tenant, editable por `TenantAdmin`. Sigue la convención dura del proyecto (nada de negocio hardcodeado) y responde directo a la decisión del usuario ("debería parametrizarlo el administrador de la automotora"). Un solo registro por tenant (`pool_pct`, `captacion_pct`, `venta_pct`).

Alternativa descartada: constantes en código o variables de entorno. Obligarían a un despliegue por cada ajuste comercial y romperían la convención.

### 2. La comisión del ejecutivo se congela al vender, no se deriva en lectura

Al registrar la venta se generan filas en `comisiones` con el `monto` ya calculado y los porcentajes usados guardados en la propia fila (`pool_pct`, `porcentaje_aplicado`). No se recalcula en cada lectura.

Es la misma razón que en el resto del sistema (comisión del acta, tramos de fidelidad): la comisión es plata que se le debe a una persona; si cambiara sola al mover un parámetro o corregir un precio, el histórico y lo ya pagado dejarían de cuadrar. Congelar hace los montos reproducibles y auditables.

### 3. Dos filas por venta (captación + venta), no una con dos beneficiarios

Cada venta genera dos `comisiones`: una `CAPTACION` (beneficiario = captador) y una `VENTA` (beneficiario = vendedor). En venta propia son la misma persona, pero siguen siendo dos filas.

Alternativa descartada: una fila con captador y vendedor. Dos filas permiten que cada beneficiario consulte "mis comisiones" con un simple `WHERE beneficiario_user_id = yo`, liquidar cada parte por separado, y reflejar la comisión cruzada de la derivación sin lógica especial.

### 4. Generación dentro de `registrar-venta`, en la misma transacción

Las comisiones se crean junto con la transición a `VENDIDO`, no en un proceso aparte. Así no hay ventas sin comisión ni desfases. Si el tenant no tiene `parametros_comision` (no debería, el seed lo crea), se usa un default seguro y se registra en auditoría.

### 5. Liquidación por orden de pago agrupada (mensual)

Al ejecutivo no se le paga comisión por comisión: acumula varias y se le pagan **agrupadas por período** (típicamente mensual), junto con su mínimo. Por eso la liquidación es una `ordenes_pago` (beneficiario, período, fecha de pago definida por el administrador, `monto_comisiones`, `monto_base`/mínimo, `monto_total`). Crear la orden toma las comisiones `PENDIENTE` del ejecutivo en el período, las asocia a la orden y las marca `PAGADA`.

El `estado_pago` de la comisión (catálogo `PENDIENTE`/`PAGADA`) se mantiene para la vista del ejecutivo y para el filtro; el vínculo `orden_pago_id` en la comisión conecta cada pago con su orden. El `monto_base` (mínimo) lo ingresa el administrador: el sistema no calcula sueldos, solo lo registra para que la orden refleje el pago total (mínimo + comisiones). Esto conecta con el ítem de menú `liq_ordenes` ("Órdenes de Pago") que ya existe.

Alternativa descartada: marcar cada comisión pagada por separado. No refleja cómo se paga en la práctica (un pago mensual por persona) ni permite el comprobante agrupado.

### 6. `/comisiones` es la vista del beneficiario; Management ve todas

El mismo endpoint sirve a ambos: `Sales` recibe solo lo suyo; los transversales, todo el tenant (para liquidar). Coherente con el patrón `?mine` del resto del sistema.

## Risks / Trade-offs

- **Cambiar los porcentajes no afecta lo ya generado** → Es intencional (Decisión 2), pero el `TenantAdmin` debe entender que el ajuste rige hacia adelante. La UI de `/config/comisiones` lo advierte.

- **Comisión sobre una venta que luego se corrige** → Hoy no hay "editar venta" tras `VENDIDO` (el acta queda cerrada). Si en el futuro se permite anular/corregir una venta, habrá que anular o regenerar sus comisiones; queda fuera de alcance y anotado.

- **Redondeo del reparto** → `comisión_empresa × pool × split` puede no ser entero. Se redondea cada fila a peso; la suma captación+venta puede diferir en $1 del pool teórico. Aceptable para incentivos; si se quiere cuadre exacto, se asigna el residuo a la fila de venta.

- **Un solo registro de parámetros por tenant** → No hay historial de vigencia de parámetros. Como los montos se congelan en cada comisión, no se necesita: la "vigencia" queda implícita en lo que cada comisión guardó.

## Migration Plan

1. Migración Alembic posterior a la última de `vehiculo-entidad-fuerte`: catálogos `tipos_comision_ejecutivo` y `estados_pago_comision`; maestra `parametros_comision`; operacional `comisiones`.
2. Seed: catálogos, y un `parametros_comision` por tenant con `20 / 40 / 60`.
3. Backfill (opcional): generar comisiones para las ventas ya registradas usando los parámetros por defecto, marcadas `PENDIENTE`. Si se omite, solo las ventas futuras generan comisión.
4. Backend (servicio + endpoints + generación en registrar-venta) y backoffice en el mismo despliegue.

## Open Questions

- **Reversa de pago (PAGADA → PENDIENTE / anular una orden):** confirmado por el usuario que **no** entra ahora, pero se deja anotado como algo a tocar a futuro (ej. corregir una orden emitida por error, que debería desasociar sus comisiones y devolverlas a `PENDIENTE`).
- ¿El monto base (mínimo) debería tomarse de un dato del usuario (sueldo base configurado) en vez de ingresarlo el administrador en cada orden? Por ahora lo ingresa el administrador; modelar el sueldo base es materia de un módulo de remuneraciones, fuera de alcance.
- ¿El captador de una venta derivada debería ver la comisión de venta (de otro) además de su captación? Por ahora cada uno ve solo lo suyo; el detalle del acta ya muestra captador y vendedor.
