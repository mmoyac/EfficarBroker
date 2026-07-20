## ADDED Requirements

### Requirement: Catálogo de checklist de 12 puntos
El sistema SHALL modelar los 12 puntos de documentos y accesorios del acta como una tabla catálogo `checklist_items` (con indicador de si requieren fecha de vencimiento) y exponerlos vía `GET /api/v1/checklist-items`.

#### Scenario: Obtener los puntos del checklist
- **WHEN** un usuario autorizado consulta `GET /api/v1/checklist-items`
- **THEN** recibe los 12 puntos del catálogo, cada uno con su indicador de vencimiento

### Requirement: Levantar el acta de recepción
El sistema SHALL exponer `POST /api/v1/vehiculos` que, en una sola operación, registra al cliente (reutilizando por RUT dentro del tenant), crea el vehículo en estado `RECEPCIONADO`, guarda el checklist y la orden de venta, y registra como captador al usuario autenticado. SHALL estar restringido a `Sales`/`Management`/`TenantAdmin` y scopeado al tenant efectivo.

#### Scenario: Creación exitosa del acta
- **WHEN** un ejecutivo `Sales` envía un acta válida (cliente, vehículo, checklist, orden de venta)
- **THEN** el sistema responde `201`, el vehículo queda en `RECEPCIONADO`, asociado al tenant efectivo y con el captador igual al usuario autenticado

#### Scenario: PPU duplicada en el tenant
- **WHEN** se levanta un acta con una PPU ya existente en el mismo tenant
- **THEN** el sistema responde `409`

#### Scenario: Reutilización de cliente por RUT
- **WHEN** se levanta un acta con un RUT ya registrado en el tenant
- **THEN** el sistema reutiliza ese cliente en lugar de duplicarlo

#### Scenario: Auditoría de la recepción
- **WHEN** se crea el acta
- **THEN** se inserta un registro en `logs_auditoria` con `estado_nuevo = RECEPCIONADO`, el usuario y el tenant

#### Scenario: Rol no autorizado
- **WHEN** un usuario con rol `Client` intenta crear un acta
- **THEN** el sistema responde `403`

### Requirement: Listar y ver vehículos del tenant
El sistema SHALL exponer `GET /api/v1/vehiculos` (lista scopeada al tenant efectivo, con `?mine=true` para filtrar por el captador autenticado) y `GET /api/v1/vehiculos/{id}` (detalle con checklist), sin exponer vehículos de otro tenant.

#### Scenario: Mis captaciones
- **WHEN** un ejecutivo consulta `GET /api/v1/vehiculos?mine=true`
- **THEN** recibe solo los vehículos cuyo captador es él mismo

#### Scenario: Aislamiento entre tenants
- **WHEN** se solicita por id un vehículo que pertenece a otro tenant
- **THEN** el sistema responde `404`

### Requirement: Aceptación manual de términos
El sistema SHALL exponer `POST /api/v1/vehiculos/{id}/aceptar-terminos` que transita el vehículo de `RECEPCIONADO` a `CONTRATO_ACEPTADO` y registra auditoría. SHALL rechazar la transición si el estado actual no es `RECEPCIONADO`.

#### Scenario: Transición válida
- **WHEN** se aceptan los términos de un vehículo en estado `RECEPCIONADO`
- **THEN** el vehículo pasa a `CONTRATO_ACEPTADO` y se registra en auditoría el cambio de estado

#### Scenario: Transición inválida
- **WHEN** se intenta aceptar términos de un vehículo que no está en `RECEPCIONADO`
- **THEN** el sistema responde `409`

### Requirement: Documento PDF de firma (Acta + Orden de Venta)
El sistema SHALL exponer `GET /api/v1/vehiculos/{id}/documento-firma` para descargar un PDF imprimible cuando el vehículo esté al menos en `CONTRATO_ACEPTADO`. El documento SHALL consolidar Acta de Recepción y Orden de Venta para firma presencial del cliente.

#### Scenario: Descarga permitida desde contrato aceptado
- **WHEN** un usuario autorizado solicita `GET /api/v1/vehiculos/{id}/documento-firma` y el vehículo está en `CONTRATO_ACEPTADO` o posterior
- **THEN** el sistema responde `200` con `Content-Type: application/pdf`

#### Scenario: Descarga bloqueada por estado
- **WHEN** se solicita el documento para un vehículo en `RECEPCIONADO` o `PROSPECTO`
- **THEN** el sistema responde `409`

#### Scenario: Contenido mínimo obligatorio del PDF
- **WHEN** se genera el documento
- **THEN** incluye, en secciones separadas: datos del cliente, datos del vehículo, condiciones de orden de venta (precio pactado, vigencia, abono), checklist de recepción y espacios de firma de cliente/ejecutivo

#### Scenario: Estándar de formato del PDF
- **WHEN** se genera el documento
- **THEN** el layout cumple estándar corporativo: encabezado con título y fecha, tipografía legible para impresión, bloques con jerarquía visual clara, y pie con texto legal breve

### Requirement: Backoffice — formulario de acta y captaciones
El backoffice SHALL ofrecer en `/actas/nueva` un formulario que captura cliente, vehículo, checklist de 12 puntos y orden de venta, y en `/captaciones` una lista de los vehículos del ejecutivo con la acción de aceptar términos.

#### Scenario: Crear un acta desde la UI
- **WHEN** un ejecutivo completa y envía el formulario de "Nueva Acta de Recepción"
- **THEN** el vehículo aparece en "Mis Captaciones" en estado `RECEPCIONADO`
