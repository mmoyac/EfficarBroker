## MODIFIED Requirements

### Requirement: Definición de la sucursal de venta en el acta
El sistema SHALL registrar en cada **acta de recepción** una `sucursal_venta_id` (FK a `sucursales` del mismo tenant) además de la `sucursal_id` de origen/captación. Al levantar el acta (`POST /api/v1/actas`), el captador SHALL indicar la sucursal de venta: si coincide con la de origen la venta es propia; si difiere, el acta queda **derivada**. La `sucursal_venta_id` SHALL ser obligatoria y pertenecer al tenant efectivo. La derivación SHALL ser una propiedad de cada recepción: un mismo vehículo puede derivarse en una recepción y no en la siguiente.

#### Scenario: Venta propia (misma sucursal)
- **WHEN** un ejecutivo levanta un acta con `sucursal_venta_id` igual a la sucursal de origen
- **THEN** el acta se crea con ambas sucursales iguales y `derivado = false`

#### Scenario: Derivación a otra sucursal
- **WHEN** un ejecutivo de Rancagua levanta un acta indicando sucursal de venta Santiago
- **THEN** el acta se crea con `sucursal_id` = Rancagua, `sucursal_venta_id` = Santiago y `derivado = true`, sin asignar vendedor nominal

#### Scenario: Sucursal de venta de otro tenant
- **WHEN** se envía una `sucursal_venta_id` que no pertenece al tenant efectivo
- **THEN** el sistema responde `400`

#### Scenario: Backfill de actas existentes
- **WHEN** se aplica la migración sobre actas previas que solo tenían `sucursal_id`
- **THEN** cada acta queda con `sucursal_venta_id = sucursal_id` (venta propia, no derivada)

#### Scenario: Derivación distinta entre recepciones del mismo auto
- **WHEN** un auto se capta en Rancagua sin derivar y años después se recapta en Rancagua derivando a Santiago
- **THEN** cada acta conserva su propia configuración de sucursales

### Requirement: Exposición de sucursal de venta y estado de derivación
El sistema SHALL exponer en `ActaOut`/`ActaDetailOut` la sucursal de venta (`sucursal_venta`) y un indicador `derivado` calculado como `sucursal_venta_id != sucursal_id`.

#### Scenario: Detalle de acta derivada
- **WHEN** se consulta el detalle de un acta derivada
- **THEN** la respuesta incluye el nombre de la sucursal de venta y `derivado = true`

### Requirement: Bandeja de ventas derivadas por sucursal
El sistema SHALL exponer `GET /api/v1/actas?derivadas=true` que lista, para un ejecutivo `Sales`, las actas activas vendibles cuya `sucursal_venta_id` es la sucursal del ejecutivo y cuya `sucursal_id` (origen) es otra distinta. Los roles transversales (`Management`/`TenantAdmin`/`SuperAdmin`) SHALL ver todas las derivaciones del tenant. Las actas cerradas SHALL quedar excluidas de la bandeja.

#### Scenario: Ejecutivo ve actas derivadas a su sucursal
- **WHEN** un ejecutivo de Santiago consulta `GET /api/v1/actas?derivadas=true`
- **THEN** recibe las actas activas captadas en otra sucursal cuya sucursal de venta es Santiago

#### Scenario: No ve derivaciones de otra sucursal
- **WHEN** un ejecutivo de Santiago consulta la bandeja de derivadas
- **THEN** NO recibe actas cuya sucursal de venta sea Rancagua

#### Scenario: Rol transversal ve todas las derivaciones
- **WHEN** `Management` consulta `GET /api/v1/actas?derivadas=true`
- **THEN** recibe todas las actas derivadas activas del tenant, sin filtrar por sucursal

#### Scenario: Acta cerrada fuera de la bandeja
- **WHEN** un acta derivada se cierra por venta
- **THEN** deja de aparecer en la bandeja de derivadas

### Requirement: Validación del vendedor por sucursal de venta
El sistema SHALL rechazar en `POST /api/v1/actas/{id}/registrar-venta` un `vendedor_user_id` cuya sucursal asignada no coincida con la `sucursal_venta_id` del acta. Esto se suma a las validaciones vigentes (vendedor `Sales` activo del mismo tenant).

#### Scenario: Vendedor de la sucursal de venta correcta
- **WHEN** se registra la venta de un acta derivada a Santiago con un vendedor cuya sucursal es Santiago
- **THEN** el sistema acepta la venta y el acta pasa a `VENDIDO`

#### Scenario: Vendedor de la sucursal equivocada
- **WHEN** se intenta registrar la venta de un acta derivada a Santiago con un vendedor cuya sucursal es Rancagua
- **THEN** el sistema responde `400` indicando que el vendedor no pertenece a la sucursal de venta

#### Scenario: Venta propia por el captador
- **WHEN** el acta no está derivada y se registra la venta con un vendedor de la misma sucursal de origen
- **THEN** el sistema acepta la venta

### Requirement: Preservación de la comisión del captador ante derivación
El sistema SHALL conservar al `captador_user_id` del acta como beneficiario de la comisión de captación aunque la venta se derive y la cierre un ejecutivo de otra sucursal. El reparto de comisión cruzada SHALL asociar la comisión de captación al captador y la de venta al vendedor efectivo **de esa acta**, independientemente de que pertenezcan a sucursales distintas y sin que recepciones anteriores del mismo vehículo afecten el reparto.

#### Scenario: Captador y vendedor de sucursales distintas
- **WHEN** un auto captado por Araneth (Rancagua) se vende por Cristian (Santiago) tras derivación
- **THEN** al pasar a `VENDIDO` quedan registrados el captador (Araneth) y el vendedor (Cristian), ambos elegibles para su respectiva comisión

#### Scenario: Comisiones aisladas entre recepciones
- **WHEN** un auto captado antes por Araneth se recapta después por Cristian y se vende
- **THEN** la comisión de captación de esa segunda venta corresponde a Cristian, sin que Araneth participe

### Requirement: Backoffice — selección de sucursal de venta y bandeja de derivadas
El backoffice SHALL permitir en `/actas/nueva` elegir entre "La venta la realizo yo" y "Derivar la venta a otra sucursal" (que habilita el selector de sucursal de venta), y SHALL ofrecer en `/captaciones/derivadas` la lista de actas derivadas a la sucursal del ejecutivo con la acción de registrar venta.

#### Scenario: Derivar desde el formulario del acta
- **WHEN** un ejecutivo marca "Derivar la venta" y selecciona una sucursal distinta a la de origen
- **THEN** el acta se crea con esa sucursal de venta y aparece en la bandeja de derivadas de la sucursal destino

#### Scenario: Tomar una venta derivada
- **WHEN** un ejecutivo de la sucursal destino abre `/captaciones/derivadas` y registra la venta de un acta derivada
- **THEN** el acta pasa a `VENDIDO` con él como vendedor
