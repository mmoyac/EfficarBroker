## ADDED Requirements

### Requirement: Listar usuarios del tenant
El sistema SHALL exponer `GET /api/v1/users` (solo `TenantAdmin`/`SuperAdmin`) que retorna los usuarios del tenant efectivo con su rol y sucursal. SHALL retornar únicamente usuarios cuyo `tenant_id` coincide con el tenant efectivo.

#### Scenario: Lista scopeada al tenant
- **WHEN** un `TenantAdmin` consulta `GET /api/v1/users`
- **THEN** recibe solo los usuarios de su propio tenant

#### Scenario: Rol no autorizado
- **WHEN** un usuario con rol `Sales` consulta `GET /api/v1/users`
- **THEN** el sistema responde `403`

### Requirement: Crear usuario
El sistema SHALL exponer `POST /api/v1/users` que crea un usuario en el tenant efectivo con nombre, email, rol (FK) y sucursal opcional. La contraseña inicial SHALL ser `admin123` (dev). El email SHALL ser único por tenant. NO SHALL permitirse asignar el rol `SuperAdmin`.

#### Scenario: Creación exitosa
- **WHEN** un `TenantAdmin` crea un usuario con datos válidos y email no usado en el tenant
- **THEN** el sistema responde `201` con el usuario creado, asociado al tenant efectivo, y puede autenticarse con `admin123`

#### Scenario: Email duplicado en el tenant
- **WHEN** se crea un usuario con un email ya existente en el mismo tenant
- **THEN** el sistema responde `409`

#### Scenario: Rol SuperAdmin no asignable
- **WHEN** se intenta crear un usuario con rol `SuperAdmin`
- **THEN** el sistema responde `400`

### Requirement: Editar usuario
El sistema SHALL exponer `PATCH /api/v1/users/{id}` para editar nombre, teléfono, rol, sucursal y estado activo de un usuario del tenant efectivo. NO SHALL permitir editar usuarios de otro tenant.

#### Scenario: Edición dentro del tenant
- **WHEN** un `TenantAdmin` edita el rol de un usuario de su tenant
- **THEN** el cambio se persiste y se refleja en la respuesta

#### Scenario: Usuario de otro tenant
- **WHEN** se intenta editar por id un usuario que pertenece a otro tenant
- **THEN** el sistema responde `404`

#### Scenario: No desactivar la propia cuenta
- **WHEN** un administrador intenta desactivar su propia cuenta
- **THEN** el sistema responde `400` y no la desactiva

### Requirement: Resetear contraseña
El sistema SHALL exponer `POST /api/v1/users/{id}/reset-password` que restablece la contraseña del usuario a `admin123` (dev), dentro del tenant efectivo.

#### Scenario: Reset exitoso
- **WHEN** un `TenantAdmin` resetea la contraseña de un usuario de su tenant
- **THEN** el usuario puede autenticarse con `admin123`

### Requirement: Catálogos de apoyo scopeados
El sistema SHALL exponer `GET /api/v1/roles` (roles asignables, excluyendo `SuperAdmin`) y `GET /api/v1/sucursales` (sucursales del tenant efectivo) para poblar los formularios.

#### Scenario: Roles asignables sin SuperAdmin
- **WHEN** se consulta `GET /api/v1/roles`
- **THEN** la lista NO incluye el rol `SuperAdmin`

#### Scenario: Sucursales del tenant efectivo
- **WHEN** un `TenantAdmin` consulta `GET /api/v1/sucursales`
- **THEN** recibe solo las sucursales de su propio tenant

### Requirement: Tenant efectivo requerido
Cuando un `SuperAdmin` no tiene un tenant activo seleccionado, los endpoints de gestión de usuarios SHALL responder `409` indicando que debe seleccionar un tenant.

#### Scenario: SuperAdmin en vista plataforma
- **WHEN** un `SuperAdmin` sin tenant activo consulta o crea usuarios
- **THEN** el sistema responde `409` pidiendo seleccionar un tenant

### Requirement: Página de gestión de usuarios en el backoffice
El backoffice SHALL ofrecer en `/config/usuarios` una tabla de usuarios del tenant con acciones para crear, editar, activar/desactivar y resetear contraseña, e indicar el uso de cupo (usados/límite).

#### Scenario: Administrar usuarios desde la UI
- **WHEN** un `TenantAdmin` abre "Gestión de Usuarios"
- **THEN** ve la lista de usuarios de su tenant y puede crear uno nuevo que aparece en la tabla
