## ADDED Requirements

### Requirement: Listado de tenants para SuperAdmin
El sistema SHALL exponer `GET /api/v1/tenants` que retorna los tenants disponibles (id, nombre, dominio, activo). SHALL estar restringido al rol `SuperAdmin`.

#### Scenario: SuperAdmin lista tenants
- **WHEN** un usuario `SuperAdmin` consulta `GET /api/v1/tenants`
- **THEN** el sistema responde `200` con la lista de tenants

#### Scenario: Rol no autorizado
- **WHEN** un usuario que no es `SuperAdmin` consulta `GET /api/v1/tenants`
- **THEN** el sistema responde `403`

### Requirement: Selección de tenant activo
El sistema SHALL exponer `POST /api/v1/auth/select-tenant` (solo `SuperAdmin`) que recibe un `tenant_id`, valida que el tenant exista y esté activo, y retorna un nuevo access token que incluye el claim `active_tenant_id`.

#### Scenario: Selección exitosa
- **WHEN** un `SuperAdmin` envía un `tenant_id` válido y activo a `POST /api/v1/auth/select-tenant`
- **THEN** el sistema responde `200` con un nuevo access token cuyo claim `active_tenant_id` es el tenant seleccionado

#### Scenario: Tenant inexistente o inactivo
- **WHEN** un `SuperAdmin` envía un `tenant_id` que no existe o está inactivo
- **THEN** el sistema responde con error (`404` inexistente / `400` inactivo) y no emite token

#### Scenario: No SuperAdmin no puede seleccionar
- **WHEN** un usuario que no es `SuperAdmin` invoca `POST /api/v1/auth/select-tenant`
- **THEN** el sistema responde `403`

### Requirement: Salir a vista de plataforma
El sistema SHALL exponer `POST /api/v1/auth/exit-tenant` (solo `SuperAdmin`) que retorna un nuevo access token sin el claim `active_tenant_id`.

#### Scenario: Volver a plataforma
- **WHEN** un `SuperAdmin` con tenant activo invoca `POST /api/v1/auth/exit-tenant`
- **THEN** el sistema responde `200` con un access token sin `active_tenant_id`

### Requirement: Resolución del tenant efectivo
El contexto de tenant SHALL resolver el tenant efectivo así: para usuarios no-SuperAdmin es su `tenant_id` propio; para `SuperAdmin` es el `active_tenant_id` del token, o ninguno si no ha seleccionado. El tenant efectivo SHALL derivarse del token y no de datos enviados por el cliente.

#### Scenario: SuperAdmin operando dentro de un tenant
- **WHEN** un `SuperAdmin` con `active_tenant_id` en su token accede a un recurso scopeado por tenant
- **THEN** el tenant efectivo es el `active_tenant_id` seleccionado

#### Scenario: SuperAdmin en vista plataforma
- **WHEN** un `SuperAdmin` sin `active_tenant_id` accede
- **THEN** el tenant efectivo es ninguno (vista de plataforma)

### Requirement: `/auth/me` refleja el tenant activo
`GET /api/v1/auth/me` SHALL incluir el tenant activo (id y nombre) cuando el SuperAdmin tenga uno seleccionado, para que el frontend muestre el contexto actual.

#### Scenario: me con tenant activo
- **WHEN** un `SuperAdmin` con tenant activo consulta `GET /api/v1/auth/me`
- **THEN** la respuesta indica el tenant activo seleccionado

### Requirement: Backoffice — vista de plataforma y switcher
El backoffice SHALL mostrar al `SuperAdmin`, tras el login y sin tenant activo, una vista de plataforma con el directorio de tenants para "entrar". SHALL ofrecer un switcher para cambiar de tenant o volver a la vista de plataforma. Los usuarios no-SuperAdmin NO SHALL ver estos elementos.

#### Scenario: SuperAdmin ve la vista de plataforma
- **WHEN** un `SuperAdmin` inicia sesión y no tiene tenant activo
- **THEN** el backoffice muestra el directorio de tenants para seleccionar uno

#### Scenario: Usuario normal no ve el selector
- **WHEN** un usuario con rol distinto de `SuperAdmin` inicia sesión
- **THEN** el backoffice no muestra vista de plataforma ni switcher de tenant
