## MODIFIED Requirements

### Requirement: Datos de venta en el acta
El **acta de recepción** SHALL poder almacenar `vendedor_user_id`, `precio_venta_final` y `fecha_venta`, que se completan al registrar la venta y permanecen vacíos antes. Estos datos SHALL pertenecer al acta y no al vehículo, de modo que cada recepción conserve el desenlace de su propia gestión.

#### Scenario: Acta aún no vendida
- **WHEN** se inspecciona un acta cuya venta no se ha registrado
- **THEN** `vendedor_user_id`, `precio_venta_final` y `fecha_venta` están vacíos

#### Scenario: Ventas históricas de un mismo vehículo
- **WHEN** un auto se vendió en 2024 y vuelve a venderse en 2026
- **THEN** cada acta conserva su propio vendedor, precio final y fecha, y ambas ventas son consultables

### Requirement: Registrar la venta
El sistema SHALL exponer `POST /api/v1/actas/{id}/registrar-venta` (roles `Sales`/`Management`/`TenantAdmin`, scopeado al tenant efectivo) que recibe `vendedor_user_id` y `precio_venta_final`, asigna el vendedor, fija el precio final y `fecha_venta`, transita el acta a `VENDIDO` y la marca como cerrada, registrando historial de estado y auditoría. Al cerrarse, el sistema SHALL resolver el abono de exclusividad aplicándolo a la comisión.

#### Scenario: Venta registrada
- **WHEN** se registra la venta de un acta en `CONTRATO_ACEPTADO` con un vendedor válido y precio final
- **THEN** el acta pasa a `VENDIDO`, con `vendedor_user_id`, `precio_venta_final` y `fecha_venta` seteados, y se registra el historial

#### Scenario: Cierre libera el vehículo para un futuro reingreso
- **WHEN** se registra la venta de un acta
- **THEN** el acta queda cerrada y el vehículo admite un acta nueva en el futuro sin conflicto de PPU

#### Scenario: Resolución del abono al vender
- **WHEN** se registra la venta de un acta con abono de exclusividad en `NO_DEVENGADO`
- **THEN** el abono pasa a `APLICADO_COMISION` y el saldo de comisión a cobrar al cierre es `comisión_pactada − abono`

#### Scenario: Transición inválida
- **WHEN** se intenta registrar la venta de un acta en estado `RECEPCIONADO` o ya `VENDIDO`
- **THEN** el sistema responde `409`

#### Scenario: Vendedor inválido
- **WHEN** el `vendedor_user_id` no es un usuario de ventas activo del tenant
- **THEN** el sistema responde `400`

#### Scenario: Captador y vendedor distintos
- **WHEN** Araneth es la captadora y se registra la venta con Cristian como vendedor
- **THEN** el acta queda con captador Araneth y vendedor Cristian

### Requirement: Backoffice — registrar venta en captaciones
El backoffice SHALL permitir, desde `/actas` y "Mis Captaciones", registrar la venta de un acta elegible seleccionando el vendedor e ingresando el precio final, y SHALL mostrar el captador, el vendedor y la comisión neta a cobrar al cierre una vez descontado el abono.

#### Scenario: Registrar venta desde la UI
- **WHEN** un ejecutivo registra la venta de un acta elegible eligiendo vendedor y precio
- **THEN** el acta aparece como `VENDIDO` con su vendedor asignado

#### Scenario: Comisión neta visible al cerrar
- **WHEN** se confirma la venta de un acta con abono de exclusividad
- **THEN** la UI muestra la comisión pactada, el abono descontado y el saldo neto a cobrar al cliente

## ADDED Requirements

### Requirement: Cierre de acta sin venta
El sistema SHALL exponer `POST /api/v1/actas/{id}/cerrar-sin-venta` (roles `Sales`/`Management`/`TenantAdmin`) que cierra un acta activa cuando el dueño desiste o vende el auto por fuera, registrando el motivo, transitando el abono a `RETENIDO` y liberando al vehículo para un futuro reingreso.

#### Scenario: Cierre por desistimiento
- **WHEN** se cierra sin venta un acta activa indicando el motivo
- **THEN** el acta queda cerrada con su motivo, el abono pasa a `RETENIDO` y se registra historial y auditoría

#### Scenario: El vehículo queda disponible
- **WHEN** un acta se cierra sin venta
- **THEN** el mismo vehículo admite un acta nueva sin conflicto de PPU

#### Scenario: Acta ya cerrada
- **WHEN** se intenta cerrar sin venta un acta que ya está cerrada
- **THEN** el sistema responde `409`
