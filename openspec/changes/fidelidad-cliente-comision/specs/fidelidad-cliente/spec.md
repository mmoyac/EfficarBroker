## ADDED Requirements

### Requirement: Maestra de tramos de fidelidad
El sistema SHALL modelar los tramos de fidelidad como maestra administrable `tramos_fidelidad` por tenant, con `nombre`, `min_vehiculos_vendidos`, `max_vehiculos_vendidos` (opcional, nulo = sin tope) y `tipo_comision_id`. Los tramos SHALL cubrir el rango de conteos sin solaparse ni dejar huecos, y SHALL exponerse vía `GET /api/v1/tramos-fidelidad`.

#### Scenario: Configuración inicial
- **WHEN** se consulta el catálogo de tramos de un tenant recién sembrado
- **THEN** existe un tramo `0–1` vehículos vendidos → Estándar 5% y un tramo `2+` → Gold 3%

#### Scenario: TenantAdmin edita un tramo
- **WHEN** `TenantAdmin` modifica el umbral o el tipo de comisión de un tramo
- **THEN** el cambio se persiste, se registra en auditoría y aplica solo a actas futuras

#### Scenario: Tramos solapados rechazados
- **WHEN** se intenta guardar un tramo cuyo rango se solapa con otro existente
- **THEN** el sistema responde `400` indicando el conflicto

#### Scenario: Hueco en la cobertura rechazado
- **WHEN** se intenta guardar una configuración de tramos que deja un conteo sin tramo asignado
- **THEN** el sistema responde `400`

#### Scenario: Rol no autorizado
- **WHEN** un usuario `Sales` intenta modificar un tramo
- **THEN** el sistema responde `403`

### Requirement: Conteo de vehículos vendidos por cliente
El sistema SHALL contar, para cada cliente dentro del tenant, la cantidad de actas cerradas con venta concretada. El conteo SHALL ser de por vida, sin ventana temporal. Las actas activas y las cerradas sin venta NO SHALL sumar.

#### Scenario: Solo suman las ventas concretadas
- **WHEN** un cliente tiene 2 actas vendidas, 1 acta activa y 1 acta cerrada sin venta
- **THEN** su conteo de vehículos vendidos es 2

#### Scenario: Sin ventana temporal
- **WHEN** un cliente vendió un auto hace cuatro años y otro el mes pasado
- **THEN** ambos suman y su conteo es 2

#### Scenario: Reingreso del mismo vehículo
- **WHEN** un cliente vendió el mismo auto en dos oportunidades distintas a través de la empresa
- **THEN** cada venta concretada suma por separado

#### Scenario: Aislamiento entre tenants
- **WHEN** un cliente con el mismo RUT opera en dos tenants
- **THEN** cada tenant cuenta solo sus propias operaciones

### Requirement: Resolución automática del tipo de comisión
Al levantar un acta, el sistema SHALL determinar el tramo del cliente según su conteo de vehículos vendidos y aplicar el `tipo_comision` de ese tramo. La respuesta SHALL incluir la tasa resuelta, el tramo aplicado y el conteo que lo justificó.

#### Scenario: Cliente nuevo
- **WHEN** se levanta el acta de un cliente sin ventas previas
- **THEN** el conteo es 0, aplica el tramo `0–1` y el tipo de comisión es Estándar 5%

#### Scenario: Tercer vehículo accede al beneficio
- **WHEN** se levanta el acta de un cliente con 2 vehículos ya vendidos
- **THEN** aplica el tramo `2+` y el tipo de comisión es Gold 3%

#### Scenario: Segundo vehículo aún sin beneficio
- **WHEN** se levanta el acta de un cliente con 1 vehículo vendido
- **THEN** aplica el tramo `0–1` y el tipo de comisión es Estándar 5%

#### Scenario: Ingresos sin venta no dan beneficio
- **WHEN** se levanta el tercer acta de un cliente que ingresó 2 autos pero no vendió ninguno
- **THEN** el conteo es 0 y NO se aplica el beneficio

### Requirement: Congelamiento del tramo en el acta
El sistema SHALL persistir en el acta el `tipo_comision_id` resuelto, el conteo de vehículos vendidos al momento de firmar y el origen de la resolución mediante FK al catálogo `origenes_tipo_comision` (`TRAMO`, `OVERRIDE`). Operaciones posteriores del cliente NO SHALL modificar la comisión de actas ya levantadas, porque el cliente firmó un contrato con una comisión determinada.

#### Scenario: Acta anterior no cambia al subir de tramo
- **WHEN** un cliente con acta vigente al 5% concreta la venta de otro auto y pasa al tramo Gold
- **THEN** el acta vigente conserva su 5% y solo las actas nuevas usan el 3%

#### Scenario: Cambio de configuración no afecta lo firmado
- **WHEN** `TenantAdmin` cambia el umbral de un tramo
- **THEN** las actas ya levantadas conservan el tipo de comisión con el que se firmaron

#### Scenario: Trazabilidad de la resolución
- **WHEN** se consulta el detalle de un acta
- **THEN** se informa el tipo de comisión aplicado, si provino del tramo o de un override, y el conteo de vehículos vendidos al firmar

### Requirement: Override supervisado del tipo de comisión
El sistema SHALL permitir a `Management`/`TenantAdmin` forzar en el acta un tipo de comisión distinto al resuelto por el tramo, exigiendo un motivo y registrando el cambio en `logs_auditoria`. Los usuarios `Sales` NO SHALL poder hacerlo.

#### Scenario: Override autorizado
- **WHEN** `Management` levanta un acta forzando Gold sobre un cliente que resolvía Estándar, con motivo
- **THEN** el acta queda con Gold, marcada como resuelta por override, y se registra el motivo en auditoría

#### Scenario: Override sin motivo
- **WHEN** se envía un override sin motivo
- **THEN** el sistema responde `400`

#### Scenario: Ejecutivo intenta forzar la tasa
- **WHEN** un usuario `Sales` envía un tipo de comisión distinto al resuelto
- **THEN** el sistema responde `403` y la comisión NO se altera

### Requirement: Ficha de fidelidad del cliente
El sistema SHALL exponer `GET /api/v1/clientes/{id}/fidelidad`, scopeado al tenant efectivo, con el conteo de vehículos vendidos, el tramo actual, el tipo de comisión vigente y cuántos vehículos faltan para el siguiente tramo.

#### Scenario: Consulta de fidelidad
- **WHEN** un ejecutivo consulta la fidelidad de un cliente con 1 vehículo vendido
- **THEN** recibe conteo 1, tramo `0–1`, comisión Estándar 5% y que le falta 1 vehículo para el tramo Gold

#### Scenario: Cliente en el tramo máximo
- **WHEN** se consulta la fidelidad de un cliente que ya está en el tramo superior
- **THEN** se informa que no hay tramo siguiente

#### Scenario: Aislamiento entre tenants
- **WHEN** se consulta la fidelidad de un cliente de otro tenant
- **THEN** el sistema responde `404`

### Requirement: Backoffice — comisión resuelta y administración de tramos
El backoffice SHALL mostrar en `/actas/nueva` el tipo de comisión resuelto con su justificación (conteo y tramo) en lugar de un selector libre, SHALL ofrecer el override solo a roles autorizados con campo de motivo, y SHALL exponer en `/config/fidelidad` la administración de tramos para `TenantAdmin`.

#### Scenario: Ejecutivo ve la tasa resuelta
- **WHEN** un ejecutivo ingresa el RUT de un cliente con 2 vehículos vendidos
- **THEN** el formulario muestra "Gold 3% — cliente frecuente, 2 vehículos vendidos" sin permitir cambiarlo

#### Scenario: Ejecutivo no ve el override
- **WHEN** un usuario `Sales` abre el formulario de acta
- **THEN** el control de override no se ofrece

#### Scenario: Administrar tramos
- **WHEN** `TenantAdmin` abre `/config/fidelidad`
- **THEN** puede ver y editar los tramos de fidelidad con su umbral y tipo de comisión asociado
