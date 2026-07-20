## ADDED Requirements

### Requirement: Cupo de usuarios por tenant
Cada tenant SHALL tener un cupo de usuarios `max_usuarios` donde `NULL` significa ilimitado y un entero representa el máximo de usuarios activos permitidos.

#### Scenario: Cupo ilimitado por defecto
- **WHEN** se inspecciona un tenant sin cupo definido
- **THEN** `max_usuarios` es `NULL` (ilimitado)

### Requirement: Solo el SuperAdmin edita el cupo
El sistema SHALL exponer `PATCH /api/v1/tenants/{id}` restringido a `SuperAdmin` para fijar `max_usuarios` (entero o `NULL`). El `TenantAdmin` NO SHALL poder modificar el cupo de su tenant.

#### Scenario: SuperAdmin fija el cupo
- **WHEN** un `SuperAdmin` envía `max_usuarios = 10` a `PATCH /api/v1/tenants/{id}`
- **THEN** el cupo del tenant queda en 10

#### Scenario: TenantAdmin no puede editar el cupo
- **WHEN** un `TenantAdmin` invoca `PATCH /api/v1/tenants/{id}`
- **THEN** el sistema responde `403`

### Requirement: Validación de cupo al crear o reactivar usuarios
Al crear un usuario o reactivar uno desactivado, el sistema SHALL verificar que el número de usuarios activos del tenant no exceda `max_usuarios`. Si el cupo se alcanzó, SHALL responder `409` con un mensaje claro. Si `max_usuarios` es `NULL`, no SHALL haber límite.

#### Scenario: Alta bloqueada por cupo alcanzado
- **WHEN** un tenant con `max_usuarios = 3` ya tiene 3 usuarios activos y se intenta crear otro
- **THEN** el sistema responde `409` indicando que se alcanzó el límite del plan

#### Scenario: Alta permitida bajo cupo ilimitado
- **WHEN** un tenant con `max_usuarios = NULL` crea un usuario
- **THEN** el sistema lo permite sin límite

#### Scenario: Desactivar libera cupo
- **WHEN** un tenant en su límite desactiva un usuario y luego crea otro
- **THEN** la creación es permitida

### Requirement: Uso de cupo visible para el SuperAdmin
`GET /api/v1/tenants` SHALL incluir `max_usuarios` y el conteo actual de usuarios activos por tenant para que el SuperAdmin vea el uso.

#### Scenario: Directorio con uso
- **WHEN** un `SuperAdmin` consulta `GET /api/v1/tenants`
- **THEN** cada tenant incluye su `max_usuarios` y su conteo de usuarios activos
