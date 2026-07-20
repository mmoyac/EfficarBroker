## ADDED Requirements

### Requirement: Datos de venta en el vehículo
El vehículo SHALL poder almacenar `vendedor_user_id`, `precio_venta_final` y `fecha_venta`, que se completan al registrar la venta y permanecen vacíos antes.

#### Scenario: Vehículo aún no vendido
- **WHEN** se inspecciona un vehículo que no se ha vendido
- **THEN** `vendedor_user_id`, `precio_venta_final` y `fecha_venta` están vacíos

### Requirement: Registrar la venta
El sistema SHALL exponer `POST /api/v1/vehiculos/{id}/registrar-venta` (roles `Sales`/`Management`/`TenantAdmin`, scopeado al tenant efectivo) que recibe `vendedor_user_id` y `precio_venta_final`, asigna el vendedor, fija el precio final y `fecha_venta`, y transita el vehículo a `VENDIDO`, registrando historial de estado y auditoría.

#### Scenario: Venta registrada
- **WHEN** se registra la venta de un vehículo en `CONTRATO_ACEPTADO` con un vendedor válido y precio final
- **THEN** el vehículo pasa a `VENDIDO`, con `vendedor_user_id`, `precio_venta_final` y `fecha_venta` seteados, y se registra el historial

#### Scenario: Transición inválida
- **WHEN** se intenta registrar la venta de un vehículo en estado `RECEPCIONADO` o ya `VENDIDO`
- **THEN** el sistema responde `409`

#### Scenario: Vendedor inválido
- **WHEN** el `vendedor_user_id` no es un usuario de ventas activo del tenant
- **THEN** el sistema responde `400`

#### Scenario: Captador y vendedor distintos
- **WHEN** Araneth es la captadora y se registra la venta con Cristian como vendedor
- **THEN** el vehículo queda con captador Araneth y vendedor Cristian

### Requirement: Equipo de ventas para selección
El sistema SHALL exponer `GET /api/v1/equipo-ventas` que lista los usuarios `Sales` activos del tenant efectivo, accesible a `Sales`/`Management`/`TenantAdmin`, para elegir al vendedor.

#### Scenario: Listar vendedores
- **WHEN** un ejecutivo consulta `GET /api/v1/equipo-ventas`
- **THEN** recibe los usuarios de ventas activos de su tenant

### Requirement: Sucursales accesibles a ejecutivos
`GET /api/v1/sucursales` SHALL ser accesible a los roles `Sales`/`Management`/`TenantAdmin`, para que el ejecutivo pueda seleccionar la sucursal de recepción al levantar el acta.

#### Scenario: Sales lista sucursales
- **WHEN** un usuario `Sales` consulta `GET /api/v1/sucursales`
- **THEN** recibe las sucursales de su tenant (no `403`)

### Requirement: Backoffice — registrar venta en captaciones
El backoffice SHALL permitir, desde "Mis Captaciones", registrar la venta de un vehículo elegible seleccionando el vendedor e ingresando el precio final, y SHALL mostrar el captador y el vendedor.

#### Scenario: Registrar venta desde la UI
- **WHEN** un ejecutivo registra la venta de un vehículo elegible eligiendo vendedor y precio
- **THEN** el vehículo aparece como `VENDIDO` con su vendedor asignado
