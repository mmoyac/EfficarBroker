## ADDED Requirements

### Requirement: Catálogo de roles
El sistema SHALL definir cinco roles: `SuperAdmin`, `TenantAdmin`, `Management`, `Sales` y `Client`. Cada usuario SHALL tener exactamente un rol asignado.

#### Scenario: Roles disponibles tras el seed
- **WHEN** se consulta el catálogo de roles luego del seed
- **THEN** existen los cinco roles y cada usuario del seed tiene uno asignado

### Requirement: Autorización por rol en endpoints
El sistema SHALL proteger los endpoints mediante guards que verifican el rol del usuario a partir del claim `role` del token. Un usuario cuyo rol no está autorizado para un endpoint SHALL recibir `403`.

#### Scenario: Rol autorizado accede
- **WHEN** un usuario con rol `TenantAdmin` accede a un endpoint restringido a `TenantAdmin`
- **THEN** el sistema procesa la petición normalmente

#### Scenario: Rol no autorizado bloqueado
- **WHEN** un usuario con rol `Sales` accede a un endpoint restringido a `TenantAdmin`
- **THEN** el sistema responde `403` y no ejecuta la operación

### Requirement: Alcance de cada rol
`SuperAdmin` SHALL operar a nivel de plataforma (multi-tenant). `TenantAdmin`, `Management`, `Sales` y `Client` SHALL operar únicamente dentro de su propio tenant. `Client` SHALL tener acceso limitado a la información de su propio contexto.

#### Scenario: TenantAdmin acotado a su tenant
- **WHEN** un `TenantAdmin` del tenant A intenta acceder a datos administrativos del tenant B
- **THEN** el sistema no expone los datos del tenant B
