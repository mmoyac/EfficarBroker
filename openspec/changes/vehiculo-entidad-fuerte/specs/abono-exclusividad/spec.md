## ADDED Requirements

### Requirement: Estados del abono de exclusividad
El sistema SHALL modelar los estados del abono de exclusividad como tabla catálogo `estados_abono`, con al menos: `NO_DEVENGADO` (cobrado al firmar, aún no ganado), `APLICADO_COMISION` (la venta se concretó y el abono se descontó de la comisión) y `RETENIDO` (venta externa o desistimiento del dueño; la empresa lo conserva como ingreso por gestión). El acta SHALL referenciar su estado de abono mediante FK.

#### Scenario: Catálogo disponible
- **WHEN** un usuario autorizado consulta `GET /api/v1/estados-abono`
- **THEN** recibe los estados del catálogo con su código y nombre

#### Scenario: Abono nace no devengado
- **WHEN** se levanta un acta con un abono de exclusividad mayor a cero
- **THEN** el acta queda con estado de abono `NO_DEVENGADO` y con la fecha de cobro registrada

### Requirement: Aplicación del abono al concretarse la venta
Al registrarse la venta de un acta, el sistema SHALL transitar el abono a `APLICADO_COMISION`, registrar la fecha de aplicación y calcular el saldo de comisión a cobrar al cierre como `comisión_pactada − abono_exclusividad`, conforme a la cláusula QUINTA del acta firmada. El abono NO SHALL generar una salida de caja hacia el cliente.

#### Scenario: Venta concretada con abono vigente
- **WHEN** se registra la venta de un acta cuyo abono está en `NO_DEVENGADO`
- **THEN** el abono pasa a `APLICADO_COMISION`, se registra la fecha de aplicación y el saldo de comisión al cierre es `comisión_pactada − abono`

#### Scenario: Abono superior a la comisión pactada
- **WHEN** el abono de exclusividad excede la comisión calculada de la venta
- **THEN** el saldo de comisión al cierre es cero y NO se genera un monto a favor del cliente

#### Scenario: Venta sin abono
- **WHEN** se registra la venta de un acta cuyo abono es cero
- **THEN** el saldo de comisión al cierre es la comisión pactada completa y el estado de abono permanece sin efecto contable

### Requirement: Retención del abono sin venta
El sistema SHALL permitir transitar el abono a `RETENIDO` cuando el acta se cierra sin venta gestionada por la empresa (venta externa o desistimiento del dueño), reconociendo el monto como ingreso por gestión y registrando la fecha y el motivo.

#### Scenario: El dueño desiste de vender
- **WHEN** se cierra un acta por desistimiento del dueño
- **THEN** el abono pasa a `RETENIDO` con su fecha y motivo, y se reconoce como ingreso por gestión

#### Scenario: Venta externa al corredor
- **WHEN** se cierra un acta porque el dueño vendió el auto por fuera
- **THEN** el abono pasa a `RETENIDO` y el acta NO registra comisión de venta

#### Scenario: Transición inválida del abono
- **WHEN** se intenta retener o aplicar un abono que ya no está en `NO_DEVENGADO`
- **THEN** el sistema responde `409`

### Requirement: Agregados financieros del abono
El sistema SHALL exponer `GET /api/v1/abonos/resumen`, scopeado al tenant efectivo y restringido a `Management`/`TenantAdmin`/`SuperAdmin`, que separa el dinero ya ganado por la empresa del dinero todavía comprometido: total en `NO_DEVENGADO` (comprometido, sujeto a aplicarse o retenerse), total `APLICADO_COMISION` y total `RETENIDO` (ambos ingreso reconocido), con su conteo de actas y filtrable por rango de fechas y sucursal.

#### Scenario: Resumen de abonos
- **WHEN** `Management` consulta `GET /api/v1/abonos/resumen`
- **THEN** recibe los totales y conteos por cada estado de abono de su tenant

#### Scenario: Separación entre comprometido y ganado
- **WHEN** un tenant tiene 10 actas vigentes con abono y 4 actas ya vendidas
- **THEN** el resumen reporta los 10 abonos como comprometidos y los 4 como ingreso reconocido, sin sumarlos en una sola cifra

#### Scenario: Aislamiento entre tenants
- **WHEN** se consulta el resumen de abonos
- **THEN** solo se agregan actas del tenant efectivo

#### Scenario: Rol no autorizado
- **WHEN** un usuario `Sales` consulta el resumen de abonos
- **THEN** el sistema responde `403`
