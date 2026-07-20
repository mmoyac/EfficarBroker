## ADDED Requirements

### Requirement: Registro inmutable de mutaciones
El sistema SHALL registrar cada mutación relevante de datos como una fila en `logs_auditoria`. Cada fila SHALL contener `tenant_id`, id del usuario transaccional, timestamp del servidor, IP de origen, estado anterior, estado nuevo y un payload JSON con los campos modificados.

#### Scenario: Mutación genera log
- **WHEN** se ejecuta una mutación auditable sobre un recurso
- **THEN** se inserta una fila en `logs_auditoria` con `tenant_id`, usuario, timestamp del servidor, IP, estado anterior, estado nuevo y payload JSON

### Requirement: Estrategia append-only
La tabla `logs_auditoria` SHALL ser append-only. Las sentencias `UPDATE` y `DELETE` sobre `logs_auditoria` SHALL estar prohibidas y ser rechazadas a nivel de base de datos.

#### Scenario: UPDATE rechazado
- **WHEN** se intenta un `UPDATE` sobre una fila de `logs_auditoria`
- **THEN** la base de datos rechaza la operación con error

#### Scenario: DELETE rechazado
- **WHEN** se intenta un `DELETE` sobre una fila de `logs_auditoria`
- **THEN** la base de datos rechaza la operación con error

### Requirement: Aislamiento del log por tenant
Los registros de auditoría SHALL estar asociados al `tenant_id` de la operación y SHALL ser consultables solo dentro del contexto de ese tenant (salvo `SuperAdmin`).

#### Scenario: Auditoría filtrada por tenant
- **WHEN** un usuario consulta el historial de auditoría de su tenant
- **THEN** solo se retornan filas cuyo `tenant_id` coincide con el del usuario
