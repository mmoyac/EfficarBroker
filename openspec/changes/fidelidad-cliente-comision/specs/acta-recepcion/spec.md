## MODIFIED Requirements

### Requirement: Levantar el acta de recepción
El sistema SHALL exponer `POST /api/v1/actas` que, en una sola operación, registra al cliente (reutilizando por RUT dentro del tenant), obtiene o crea el vehículo por PPU dentro del tenant, crea el acta en estado `RECEPCIONADO` asociando cliente y vehículo, guarda el checklist y la orden de venta, y registra como captador al usuario autenticado. El `tipo_comision` NO SHALL recibirse como dato libre del formulario: el sistema lo resuelve desde el tramo de fidelidad del cliente y lo congela en el acta, admitiendo override solo de `Management`/`TenantAdmin` con motivo. SHALL estar restringido a `Sales`/`Management`/`TenantAdmin` y scopeado al tenant efectivo.

#### Scenario: Creación exitosa del acta
- **WHEN** un ejecutivo `Sales` envía un acta válida (cliente, vehículo, checklist, orden de venta)
- **THEN** el sistema responde `201`, el acta queda en `RECEPCIONADO`, asociada al tenant efectivo, con el captador igual al usuario autenticado y con el tipo de comisión resuelto por el tramo de fidelidad del cliente

#### Scenario: Comisión resuelta por fidelidad
- **WHEN** se levanta el acta de un cliente con 2 vehículos vendidos
- **THEN** el acta queda con el tipo de comisión del tramo `2+` y registra el conteo que lo justificó

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

### Requirement: Backoffice — formulario de acta y captaciones
El backoffice SHALL ofrecer en `/actas/nueva` un formulario que captura cliente, vehículo, checklist de 12 puntos y orden de venta, y en `/captaciones` una lista de las actas del ejecutivo con la acción de aceptar términos. Al ingresar una PPU ya conocida en el tenant, el formulario SHALL precargar los datos del vehículo y advertir que se trata de un reingreso. Al identificar al cliente por RUT, el formulario SHALL mostrar el tipo de comisión resuelto por su tramo de fidelidad, con su justificación, en lugar de un selector libre.

#### Scenario: Crear un acta desde la UI
- **WHEN** un ejecutivo completa y envía el formulario de "Nueva Acta de Recepción"
- **THEN** el acta aparece en `/actas` en estado `RECEPCIONADO`

#### Scenario: Reingreso detectado en el formulario
- **WHEN** el ejecutivo ingresa una PPU ya registrada en el tenant sin acta vigente
- **THEN** el formulario precarga marca, modelo, año, motor y chasis, y advierte que el auto ya fue corretado antes

#### Scenario: Comisión mostrada al identificar al cliente
- **WHEN** el ejecutivo ingresa el RUT de un cliente frecuente
- **THEN** el formulario muestra la tasa resuelta y el motivo (cantidad de vehículos vendidos y tramo alcanzado)
