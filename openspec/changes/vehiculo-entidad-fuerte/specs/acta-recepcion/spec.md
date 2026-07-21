## ADDED Requirements

### Requirement: Vehículo como entidad fuerte
El sistema SHALL modelar `vehiculos` como la identidad física del auto — PPU, año, N° motor, N° chasis, y las referencias a versión, color, tipo de vehículo y combustible — sin dueño, sin estado de ciclo de vida, sin captador, sin sucursales, sin orden de venta y sin datos de venta. La PPU SHALL ser única por tenant. Un vehículo SHALL poder tener múltiples actas de recepción a lo largo del tiempo.

Marca y modelo NO SHALL almacenarse como texto en el vehículo: SHALL derivarse de `version_id` a través de `vehiculo_versiones` → `vehiculo_modelos` → `vehiculo_marcas`, de modo que el catálogo sea la única fuente de verdad. `version_id` SHALL ser obligatoria.

#### Scenario: Marca y modelo derivados del catálogo
- **WHEN** se consulta la ficha de un vehículo
- **THEN** la marca y el modelo se resuelven desde su versión en el catálogo, sin columnas de texto duplicadas

#### Scenario: Corrección en el catálogo se propaga
- **WHEN** se corrige el nombre de una marca en `vehiculo_marcas`
- **THEN** todos los vehículos de esa marca reflejan el nombre corregido sin migración de datos

#### Scenario: La ficha del vehículo no cambia al cambiar de dueño
- **WHEN** un mismo auto se recepciona por segunda vez con un dueño distinto
- **THEN** la ficha del vehículo se conserva sin duplicarse y el nuevo dueño queda registrado en el acta nueva, no en el vehículo

#### Scenario: Historial de recepciones de un auto
- **WHEN** se consulta `GET /api/v1/vehiculos/{id}/actas`
- **THEN** se reciben todas las actas de ese vehículo ordenadas de la más reciente a la más antigua, cada una con su dueño, captador, fechas y desenlace

### Requirement: Una sola acta activa por vehículo
El sistema SHALL admitir como máximo un acta activa por vehículo, entendiendo por activa toda acta que no esté cerrada (vendida, retirada o anulada). Las actas cerradas SHALL conservarse íntegras como historial. La restricción SHALL estar garantizada en base de datos mediante un índice único parcial, no solo en la capa de aplicación.

#### Scenario: Reingreso de un auto ya cerrado
- **WHEN** se levanta un acta para una PPU cuyo acta anterior está cerrada
- **THEN** el sistema reutiliza la ficha del vehículo, crea un acta nueva en `RECEPCIONADO` y responde `201`

#### Scenario: Reingreso de un auto con acta vigente
- **WHEN** se levanta un acta para una PPU que ya tiene un acta activa en el tenant
- **THEN** el sistema responde `409` indicando que el vehículo ya tiene un acta vigente

#### Scenario: El historial anterior no se pisa
- **WHEN** se crea la segunda acta de un vehículo
- **THEN** el cliente, checklist, estados, fechas y datos de venta de la primera acta permanecen intactos y consultables

### Requirement: Checklist e historial de estado por acta
El sistema SHALL asociar el checklist de 12 puntos y el historial de transiciones de estado al acta de recepción y no al vehículo. Cada recepción SHALL tener su propio checklist y su propia línea de tiempo de estados.

El tipo de punto de checklist (documento/accesorio) y el estado de cada punto (OK/Faltante/Observado) SHALL modelarse como tablas catálogo `tipos_checklist_item` y `estados_checklist`, referenciadas por FK. NO SHALL persistirse como texto libre.

#### Scenario: Tipos y estados de checklist como catálogo
- **WHEN** se consultan los puntos del checklist y sus estados posibles
- **THEN** ambos provienen de tablas catálogo, no de valores fijos en el código

#### Scenario: Estado de checklist inválido
- **WHEN** se envía un estado de checklist que no existe en el catálogo
- **THEN** el sistema responde `400`

#### Scenario: Checklist independiente por recepción
- **WHEN** un auto se recepciona por segunda vez y su checklist difiere del de la primera vez
- **THEN** ambos checklists coexisten, cada uno asociado a su acta

#### Scenario: KPIs temporales por acta
- **WHEN** se calcula el tiempo de captación a venta de un auto recepcionado dos veces
- **THEN** cada acta aporta su propia duración, sin mezclar los tiempos de ambas recepciones

### Requirement: Mantención de la ficha del vehículo
El sistema SHALL exponer `PATCH /api/v1/vehiculos/{id}` para corregir la ficha física del auto, con permisos escalonados según su historial documental. Mientras el vehículo NO tenga actas firmadas (`CONTRATO_ACEPTADO` o posterior) ni cerradas, el captador de su acta activa SHALL poder corregirla. Una vez que existe un acta firmada o cerrada, solo `Management`/`TenantAdmin`/`SuperAdmin` SHALL poder editarla, con motivo obligatorio y registro en `logs_auditoria`, porque el cambio se propaga a documentos ya emitidos. La PPU SHALL ser editable únicamente por esos roles en cualquier caso, por tratarse de la identidad del vehículo.

#### Scenario: Corrección temprana por el captador
- **WHEN** el captador corrige el N° de chasis de un auto cuya única acta está en `RECEPCIONADO`
- **THEN** el sistema acepta el cambio sin exigir motivo

#### Scenario: Corrección con documento firmado
- **WHEN** `Management` corrige el N° de motor de un auto con un acta en `CONTRATO_ACEPTADO`, indicando el motivo
- **THEN** el sistema acepta el cambio y registra en auditoría el valor anterior, el nuevo, el motivo y el usuario

#### Scenario: Captador bloqueado tras la firma
- **WHEN** el captador intenta editar la ficha de un auto que ya tiene un acta firmada
- **THEN** el sistema responde `403`

#### Scenario: Motivo obligatorio con historial
- **WHEN** `Management` edita la ficha de un vehículo con actas cerradas sin indicar motivo
- **THEN** el sistema responde `400`

#### Scenario: Cambio de PPU restringido
- **WHEN** un usuario `Sales` intenta cambiar la PPU de un vehículo
- **THEN** el sistema responde `403`

#### Scenario: PPU duplicada
- **WHEN** se cambia la PPU de un vehículo a una ya existente en el tenant
- **THEN** el sistema responde `409`

#### Scenario: Vehículo con historial no se elimina
- **WHEN** se intenta eliminar un vehículo que tiene al menos un acta
- **THEN** el sistema responde `409` y la ficha se conserva

### Requirement: Backoffice — mantenedor de vehículos
El backoffice SHALL ofrecer a `Management`/`TenantAdmin`/`SuperAdmin` una entrada de menú "Vehículos" en el grupo de Validaciones y Catálogo, con una grilla de fichas del tenant buscable por PPU, y el detalle de cada ficha mostrando sus atributos físicos y el historial de actas del auto. Los usuarios `Sales` NO SHALL ver esta entrada.

#### Scenario: Management busca un auto por PPU
- **WHEN** `Management` abre el mantenedor de vehículos y busca una PPU
- **THEN** ve la ficha del auto con sus atributos físicos y todas sus actas, de la más reciente a la más antigua

#### Scenario: Edición con advertencia de impacto
- **WHEN** `Management` edita la ficha de un vehículo que tiene actas firmadas
- **THEN** la UI advierte que el cambio afecta documentos ya emitidos y exige un motivo antes de guardar

#### Scenario: Entrada oculta para ejecutivos
- **WHEN** un usuario `Sales` consulta su menú
- **THEN** la entrada "Vehículos" no aparece

### Requirement: Backoffice — grilla de actas como entrada del módulo
El backoffice SHALL ofrecer en `/actas` una grilla que lista por defecto las actas del usuario autenticado, con columnas de PPU, vehículo, cliente, estado, fecha de recepción y precio pactado, e incluir la acción "Nueva acta" hacia `/actas/nueva`. Los roles transversales (`Management`, `TenantAdmin`, `SuperAdmin`) SHALL disponer de un control para ver todas las actas del tenant con la columna de captador.

#### Scenario: Ejecutivo abre la grilla
- **WHEN** un ejecutivo `Sales` entra a `/actas`
- **THEN** ve únicamente sus propias actas y el botón "Nueva acta"

#### Scenario: Rol transversal amplía el alcance
- **WHEN** `Management` activa "ver todas del tenant" en `/actas`
- **THEN** la grilla muestra las actas de todos los captadores del tenant, con la columna de captador visible

#### Scenario: El control ampliado no está disponible para ejecutivos
- **WHEN** un usuario `Sales` abre `/actas`
- **THEN** el control para ver todas las actas del tenant no se ofrece

#### Scenario: Grilla vacía
- **WHEN** un ejecutivo sin actas entra a `/actas`
- **THEN** ve un estado vacío con la invitación a crear su primera acta

#### Scenario: Navegar al detalle
- **WHEN** el ejecutivo selecciona una fila de la grilla
- **THEN** se abre el detalle del acta con su checklist, su orden de venta y el historial de recepciones anteriores del vehículo

## MODIFIED Requirements

### Requirement: Levantar el acta de recepción
El sistema SHALL exponer `POST /api/v1/actas` que, en una sola operación, registra al cliente (reutilizando por RUT dentro del tenant), obtiene o crea el vehículo por PPU dentro del tenant, crea el acta en estado `RECEPCIONADO` asociando cliente y vehículo, guarda el checklist, la orden de venta y las observaciones, y registra como captador al usuario autenticado. La sucursal de recepción SHALL ser opcional en el cuerpo: si se omite, se usa la sucursal del usuario autenticado, y SHALL responder `400` si el usuario no tiene sucursal y no la envía. SHALL estar restringido a `Sales`/`Management`/`TenantAdmin` y scopeado al tenant efectivo.

#### Scenario: Creación exitosa del acta
- **WHEN** un ejecutivo `Sales` envía un acta válida (cliente, vehículo, checklist, orden de venta)
- **THEN** el sistema responde `201`, el acta queda en `RECEPCIONADO`, asociada al tenant efectivo y con el captador igual al usuario autenticado

#### Scenario: Sucursal de recepción por defecto
- **WHEN** un ejecutivo con sucursal asignada levanta un acta sin enviar `sucursal_id`
- **THEN** el acta se crea con la sucursal del ejecutivo como sucursal de origen

#### Scenario: Usuario sin sucursal debe indicarla
- **WHEN** un usuario sin sucursal asignada levanta un acta sin enviar `sucursal_id`
- **THEN** el sistema responde `400`

#### Scenario: Vehículo con acta vigente
- **WHEN** se levanta un acta con una PPU que ya tiene un acta activa en el mismo tenant
- **THEN** el sistema responde `409`

#### Scenario: Reutilización del vehículo por PPU
- **WHEN** se levanta un acta con una PPU ya registrada en el tenant y sin acta activa
- **THEN** el sistema reutiliza esa ficha de vehículo en lugar de duplicarla y crea un acta nueva

#### Scenario: Reutilización de cliente por RUT
- **WHEN** se levanta un acta con un RUT ya registrado en el tenant
- **THEN** el sistema reutiliza ese cliente en lugar de duplicarlo

#### Scenario: Auditoría de la recepción
- **WHEN** se crea el acta
- **THEN** se inserta un registro en `logs_auditoria` con `estado_nuevo = RECEPCIONADO`, el usuario y el tenant

#### Scenario: Rol no autorizado
- **WHEN** un usuario con rol `Client` intenta crear un acta
- **THEN** el sistema responde `403`

### Requirement: Listar y ver actas del tenant
El sistema SHALL exponer `GET /api/v1/actas` (lista scopeada al tenant efectivo, con `?mine=true` para filtrar por el captador autenticado) y `GET /api/v1/actas/{id}` (detalle con checklist, cliente, vehículo y estado del abono), sin exponer actas de otro tenant.

#### Scenario: Mis actas
- **WHEN** un ejecutivo consulta `GET /api/v1/actas?mine=true`
- **THEN** recibe solo las actas cuyo captador es él mismo

#### Scenario: Aislamiento entre tenants
- **WHEN** se solicita por id un acta que pertenece a otro tenant
- **THEN** el sistema responde `404`

### Requirement: Aceptación manual de términos
El sistema SHALL exponer `POST /api/v1/actas/{id}/aceptar-terminos` que transita el acta de `RECEPCIONADO` a `CONTRATO_ACEPTADO` y registra auditoría. SHALL rechazar la transición si el estado actual no es `RECEPCIONADO`.

#### Scenario: Transición válida
- **WHEN** se aceptan los términos de un acta en estado `RECEPCIONADO`
- **THEN** el acta pasa a `CONTRATO_ACEPTADO` y se registra en auditoría el cambio de estado

#### Scenario: Transición inválida
- **WHEN** se intenta aceptar términos de un acta que no está en `RECEPCIONADO`
- **THEN** el sistema responde `409`

### Requirement: Documento PDF de firma (Acta + Orden de Venta)
El sistema SHALL exponer `GET /api/v1/actas/{id}/documento-firma` para descargar un PDF imprimible cuando el acta esté al menos en `CONTRATO_ACEPTADO`. El documento SHALL consolidar Acta de Recepción y Orden de Venta para firma presencial del cliente, tomando los datos del acta y de su vehículo asociado.

#### Scenario: Descarga permitida desde contrato aceptado
- **WHEN** un usuario autorizado solicita `GET /api/v1/actas/{id}/documento-firma` y el acta está en `CONTRATO_ACEPTADO` o posterior
- **THEN** el sistema responde `200` con `Content-Type: application/pdf`

#### Scenario: Descarga bloqueada por estado
- **WHEN** se solicita el documento para un acta en `RECEPCIONADO` o `PROSPECTO`
- **THEN** el sistema responde `409`

#### Scenario: Contenido mínimo obligatorio del PDF
- **WHEN** se genera el documento
- **THEN** incluye, en secciones separadas: datos del cliente, datos del vehículo, condiciones de orden de venta (precio pactado, vigencia, abono), checklist de recepción, observaciones del acta y espacios de firma de cliente/ejecutivo

#### Scenario: El ejecutivo del documento es el vendedor nominado
- **WHEN** el acta está derivada a otra sucursal con un vendedor nominado y se genera el documento
- **THEN** la "Firma Ejecutivo" muestra el nombre y RUT del vendedor nominado (no del captador), y el vendedor está autorizado a descargar el documento

#### Scenario: El ejecutivo del documento en venta propia
- **WHEN** el acta no está derivada (venta propia) y se genera el documento
- **THEN** la "Firma Ejecutivo" muestra al captador, que también es el vendedor

#### Scenario: Checklist con fecha de vencimiento
- **WHEN** un punto del checklist requiere vencimiento (permiso de circulación, seguro, revisión técnica) y se registró su fecha
- **THEN** el checklist del PDF muestra en columnas separadas la fecha de recepción y la fecha de vencimiento de ese punto

#### Scenario: Observaciones del acta en el PDF
- **WHEN** el acta tiene un texto de observaciones
- **THEN** el PDF lo imprime en su sección de OBSERVACIONES

#### Scenario: Estándar de formato del PDF
- **WHEN** se genera el documento
- **THEN** el layout cumple estándar corporativo: encabezado con título y fecha, tipografía legible para impresión, bloques con jerarquía visual clara, y pie con texto legal breve

#### Scenario: El PDF corresponde a su recepción
- **WHEN** se descarga el documento de la primera acta de un auto recepcionado dos veces
- **THEN** el PDF refleja el cliente, checklist y orden de venta de esa primera recepción, no los de la segunda

### Requirement: Backoffice — formulario de acta y captaciones
El backoffice SHALL ofrecer en `/actas/nueva` un formulario que captura cliente, vehículo, checklist de 12 puntos, orden de venta y observaciones, y en `/captaciones` una lista de las actas del ejecutivo con la acción de aceptar términos. La sucursal de recepción NO SHALL pedirse: se asume la del usuario autenticado, y solo se ofrece elegirla si el usuario no tiene una asignada. Los campos de cliente (por RUT) y de vehículo (por PPU) SHALL autocompletarse a medida que se escribe.

#### Scenario: Crear un acta desde la UI
- **WHEN** un ejecutivo completa y envía el formulario de "Nueva Acta de Recepción"
- **THEN** el acta aparece en `/actas` en estado `RECEPCIONADO`, en la sucursal del ejecutivo

#### Scenario: Sucursal de recepción implícita
- **WHEN** un ejecutivo con sucursal asignada abre el formulario
- **THEN** no se le pide la sucursal de recepción y el acta se crea en la suya

#### Scenario: Autocompletar cliente por RUT
- **WHEN** el ejecutivo escribe un RUT ya registrado en el tenant
- **THEN** el formulario carga automáticamente nombre, correo, teléfono, domicilio y comuna del cliente

#### Scenario: Autocompletar vehículo por PPU (reingreso)
- **WHEN** el ejecutivo escribe una PPU ya registrada en el tenant sin acta vigente
- **THEN** el formulario precarga marca, modelo, versión, año, motor, chasis y color, y advierte que el auto ya fue corretado antes

#### Scenario: Reingreso con acta vigente bloqueado en la UI
- **WHEN** la PPU escrita ya tiene un acta vigente
- **THEN** el formulario lo advierte y bloquea el envío

### Requirement: Backoffice — edición completa del acta
El backoffice SHALL permitir editar un acta en `RECEPCIONADO` de forma completa: datos del cliente, ficha del vehículo (marca, modelo, versión, patente, año, motor, chasis, color), orden de venta, vendedor nominado, observaciones y el checklist de 12 puntos (marcar/desmarcar cada punto, su estado y su fecha de vencimiento). Los cambios de la ficha del vehículo SHALL enviarse a `PATCH /api/v1/vehiculos/{id}` y el resto a `PATCH /api/v1/actas/{id}`.

#### Scenario: Actualizar el checklist tras recibir menos accesorios
- **WHEN** el cliente entregó menos accesorios de los registrados y el ejecutivo desmarca esos puntos y guarda
- **THEN** el acta conserva el checklist actualizado

#### Scenario: Editar la ficha del auto desde el acta
- **WHEN** el ejecutivo corrige la versión o la patente en la edición del acta
- **THEN** el cambio se aplica a la ficha del vehículo y queda reflejado en el acta
