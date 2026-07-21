## ADDED Requirements

### Requirement: Parámetros de comisión administrables
El sistema SHALL modelar los parámetros de comisión del ejecutivo como una maestra `parametros_comision` por tenant, con `pool_pct` (porcentaje de la comisión de la empresa que se reparte entre los ejecutivos), `captacion_pct` y `venta_pct` (cómo se divide esa parte entre captador y vendedor). `captacion_pct + venta_pct` SHALL sumar 100. SHALL exponerse vía `GET /api/v1/parametros-comision` y editarse vía `PATCH /api/v1/parametros-comision`, restringido a `TenantAdmin`. El seed inicial SHALL ser `pool_pct = 20`, `captacion_pct = 40`, `venta_pct = 60`.

#### Scenario: Configuración inicial
- **WHEN** un tenant recién sembrado consulta sus parámetros de comisión
- **THEN** recibe `pool_pct = 20`, `captacion_pct = 40`, `venta_pct = 60`

#### Scenario: TenantAdmin ajusta los parámetros
- **WHEN** `TenantAdmin` cambia `pool_pct` a 30 y el split a 50/50
- **THEN** el cambio se persiste, se registra en auditoría y aplica solo a comisiones futuras

#### Scenario: Split inválido
- **WHEN** se intenta guardar `captacion_pct` y `venta_pct` que no suman 100
- **THEN** el sistema responde `400`

#### Scenario: Rol no autorizado
- **WHEN** un usuario `Sales` intenta editar los parámetros
- **THEN** el sistema responde `403`

### Requirement: Generación de comisiones al vender
Al registrar la venta de un acta, el sistema SHALL calcular la comisión de la empresa (`MAX(precio_venta_final × tasa, mínimo)` según el tipo de comisión del acta) y generar dos comisiones de ejecutivo: una de tipo `CAPTACION` para el captador y una de tipo `VENTA` para el vendedor. El monto de cada una SHALL ser `comisión_empresa × pool_pct/100 × (captacion_pct|venta_pct)/100`. El monto y los porcentajes usados SHALL congelarse en la comisión al momento de la venta.

#### Scenario: Venta propia (captador = vendedor)
- **WHEN** un ejecutivo capta y vende él mismo un auto
- **THEN** se generan dos comisiones a su nombre (captación y venta) cuya suma es `comisión_empresa × pool_pct/100`

#### Scenario: Venta derivada (captador ≠ vendedor)
- **WHEN** un auto captado por Araneth se vende por Cristian tras derivación
- **THEN** la comisión de captación es de Araneth y la de venta es de Cristian, cada una con su fracción

#### Scenario: Congelamiento del monto
- **WHEN** tras registrar una venta el `TenantAdmin` cambia los porcentajes
- **THEN** las comisiones ya generadas conservan su monto original

#### Scenario: Sin venta no hay comisión
- **WHEN** un acta se cierra sin venta
- **THEN** no se genera ninguna comisión de ejecutivo

#### Scenario: Nacen pendientes
- **WHEN** se generan las comisiones de una venta
- **THEN** ambas quedan en estado de pago `PENDIENTE`

### Requirement: Tipos y estados de comisión como catálogo
El tipo de comisión de ejecutivo (`CAPTACION`, `VENTA`) y el estado de pago (`PENDIENTE`, `PAGADA`) SHALL modelarse como tablas catálogo `tipos_comision_ejecutivo` y `estados_pago_comision`, referenciadas por FK. NO SHALL persistirse como texto libre.

#### Scenario: Catálogos disponibles
- **WHEN** se consultan los tipos de comisión de ejecutivo y los estados de pago
- **THEN** ambos provienen de tablas catálogo

### Requirement: Consulta de comisiones del ejecutivo
El sistema SHALL exponer `GET /api/v1/comisiones` que devuelve, para el usuario autenticado (`?mine=true` o por defecto para `Sales`), sus comisiones como captador y como vendedor, cada una con acta, PPU, vehículo, cliente, tipo, monto, estado de pago y fechas, más el total. SHALL ser filtrable por rango de fechas y por estado de pago. Los roles transversales (`Management`/`TenantAdmin`/`SuperAdmin`) SHALL poder ver todas las comisiones del tenant. Todo scopeado al tenant efectivo.

#### Scenario: El ejecutivo ve sus comisiones
- **WHEN** un ejecutivo `Sales` consulta `GET /api/v1/comisiones`
- **THEN** recibe solo las comisiones cuyo beneficiario es él mismo, cada una con su tipo (`CAPTACION` o `VENTA`) y el total

#### Scenario: Origen de la comisión visible (captación, venta o ambas)
- **WHEN** un ejecutivo captó y vendió él mismo un auto (venta propia) y consulta sus comisiones
- **THEN** ve sobre esa acta una comisión de captación y una de venta, y la vista la identifica como "ambas"; cuando solo captó (o solo vendió) un auto, la comisión aparece con su único tipo

#### Scenario: Filtro por estado de pago
- **WHEN** un ejecutivo filtra por estado `PENDIENTE`
- **THEN** recibe solo sus comisiones aún no pagadas

#### Scenario: Management ve todas
- **WHEN** `Management` consulta las comisiones del tenant
- **THEN** recibe las comisiones de todos los ejecutivos del tenant

#### Scenario: Aislamiento entre tenants
- **WHEN** se consultan las comisiones
- **THEN** solo se devuelven las del tenant efectivo

### Requirement: Liquidación por orden de pago
El pago de comisiones se hace **agrupado** por ejecutivo y período (típicamente mensual), no comisión por comisión. El sistema SHALL modelar una `ordenes_pago` por tenant con `beneficiario_user_id`, `periodo_desde`, `periodo_hasta`, `fecha_pago` (definida por el administrador), `monto_comisiones` (suma de las comisiones incluidas), `monto_base` (el mínimo/sueldo base del período, opcional, ingresado por el administrador) y `monto_total` (`monto_comisiones + monto_base`). SHALL exponer `POST /api/v1/ordenes-pago`, restringido a `Management`/`TenantAdmin`, que toma las comisiones `PENDIENTE` del beneficiario en el período, las agrupa en la orden, las marca `PAGADA` asociándolas a la orden, y registra auditoría. Una comisión ya `PAGADA` NO SHALL poder incluirse en otra orden.

#### Scenario: Crear una orden de pago mensual
- **WHEN** `Management` crea una orden de pago para un ejecutivo, un período y una fecha de pago
- **THEN** todas las comisiones `PENDIENTE` de ese ejecutivo en el período quedan `PAGADA` y asociadas a la orden, y `monto_comisiones` es su suma

#### Scenario: Mínimo más comisiones
- **WHEN** el administrador ingresa el monto base (mínimo) al crear la orden
- **THEN** `monto_total` es `monto_base + monto_comisiones`

#### Scenario: Comisiones ya pagadas no se re-agrupan
- **WHEN** se crea una orden para un período cuyas comisiones ya fueron pagadas en otra orden
- **THEN** esas comisiones no se incluyen (no se pagan dos veces)

#### Scenario: Rol no autorizado
- **WHEN** un usuario `Sales` intenta crear una orden de pago
- **THEN** el sistema responde `403`

#### Scenario: Órdenes separadas por beneficiario en venta derivada
- **WHEN** un auto captado por Araneth (Rancagua) lo vende Cristian (Santiago) y se liquidan sus comisiones
- **THEN** la comisión de captación de Araneth va en la orden de pago de Araneth y la de venta de Cristian en la de Cristian: cada ejecutivo cobra lo suyo en su propia orden

#### Scenario: Consultar órdenes de pago
- **WHEN** un ejecutivo consulta sus órdenes de pago
- **THEN** recibe sus órdenes con período, fecha de pago, monto de comisiones, base y total, y el detalle de las comisiones incluidas indicando el tipo (captación/venta) de cada una; los roles transversales ven las de todo el tenant

### Requirement: Estado de resultados para el administrador
El sistema SHALL exponer `GET /api/v1/estado-resultado` (rango de fechas, scopeado al tenant), restringido a `Management`/`TenantAdmin`/`SuperAdmin`, que consolida el desempeño del período: cantidad de autos vendidos y monto transado; comisión de la empresa (ingreso por corretaje); comisiones de ejecutivos (egreso); margen de corretaje (empresa − ejecutivos); abonos retenidos (ingreso por gestión de autos no vendidos); y abonos comprometidos (informativo). Todos los montos SHALL derivarse de las ventas y comisiones del período, sin recalcular montos congelados.

#### Scenario: Resultado del período
- **WHEN** `TenantAdmin` consulta el estado de resultados de un mes
- **THEN** recibe la cantidad de ventas, el monto transado, la comisión de la empresa, las comisiones de ejecutivos, el margen de corretaje y los abonos retenidos del período

#### Scenario: Margen de corretaje
- **WHEN** en el período la empresa cobró $1.000.000 en comisiones y pagó $200.000 a ejecutivos
- **THEN** el margen de corretaje reportado es $800.000

#### Scenario: Rol no autorizado
- **WHEN** un usuario `Sales` consulta el estado de resultados
- **THEN** el sistema responde `403`

#### Scenario: Aislamiento entre tenants
- **WHEN** se consulta el estado de resultados
- **THEN** solo se agregan ventas y comisiones del tenant efectivo

### Requirement: Backoffice — vista de comisiones y parámetros
El backoffice SHALL ofrecer en `/comisiones` una grilla de las comisiones del ejecutivo (tipo, acta/vehículo, monto, estado de pago, total, filtros por fecha y estado) y sus órdenes de pago, de solo lectura para `Sales`. SHALL ofrecer en `/config/comisiones` un formulario para que `TenantAdmin` edite `pool_pct` y el split captación/venta. Los roles transversales SHALL poder generar órdenes de pago (agrupando las comisiones pendientes de un ejecutivo en un período, con fecha de pago y mínimo) desde `/liquidaciones/ordenes`.

#### Scenario: Ejecutivo ve su historial de incentivos
- **WHEN** un ejecutivo entra a `/comisiones`
- **THEN** ve cada comisión con su tipo (captación / venta / ambas por acta), monto, estado de pago, el total, y sus órdenes de pago, sin acciones de edición

#### Scenario: Administrar los parámetros
- **WHEN** `TenantAdmin` abre `/config/comisiones`
- **THEN** puede editar el porcentaje del pool y el split captación/venta

#### Scenario: Generar una orden de pago
- **WHEN** `Management` genera desde `/liquidaciones/ordenes` la orden de un ejecutivo para un mes, con la fecha de pago y el mínimo
- **THEN** las comisiones pendientes de ese ejecutivo en el mes quedan pagadas y agrupadas en la orden, con el total mínimo + comisiones
