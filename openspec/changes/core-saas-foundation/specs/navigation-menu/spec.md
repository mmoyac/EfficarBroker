## ADDED Requirements

### Requirement: Menú modelado en tablas catálogo
La estructura del menú SHALL persistirse en tablas catálogo (`menu_secciones`, `menu_items`) con su mapeo a rol; NO SHALL estar hardcodeada en el código del backend ni del frontend. Cada ítem SHALL almacenar etiqueta, icono, ruta y orden.

#### Scenario: Menú proviene de catálogo
- **WHEN** se inspecciona el origen de la respuesta de navegación
- **THEN** el árbol se construye consultando las tablas catálogo de menú y su mapeo por rol, no una definición literal en código

### Requirement: Endpoint de menú por rol
El sistema SHALL exponer `GET /api/v1/navigation/menu` que retorna el árbol de navegación del sidebar del backoffice según el rol y tenant del usuario autenticado. Cada nodo SHALL incluir etiqueta, icono y ruta.

#### Scenario: Menú del rol Sales
- **WHEN** un usuario con rol `Sales` consulta `GET /api/v1/navigation/menu`
- **THEN** recibe las secciones de Gestión de Vehículos, Agenda de Visitas y Mis Comisiones, y NO recibe secciones de BI ni Configuración del Negocio

#### Scenario: Menú del rol TenantAdmin
- **WHEN** un usuario con rol `TenantAdmin` consulta `GET /api/v1/navigation/menu`
- **THEN** recibe las secciones de Business Intelligence y Configuración del Negocio

#### Scenario: Menú del rol Management
- **WHEN** un usuario con rol `Management` consulta `GET /api/v1/navigation/menu`
- **THEN** recibe las secciones de Control y Validaciones, Operaciones Sucursales y Módulo de Liquidaciones

### Requirement: Sin acceso sin autenticación
El endpoint de navegación SHALL requerir autenticación.

#### Scenario: Petición sin token
- **WHEN** se consulta `GET /api/v1/navigation/menu` sin access token válido
- **THEN** el sistema responde `401`

### Requirement: Sidebar del backoffice consume el endpoint
El backoffice SHALL renderizar el sidebar exclusivamente a partir de la respuesta de `GET /api/v1/navigation/menu`, sin menús hardcodeados por rol en el cliente.

#### Scenario: Sidebar refleja el rol
- **WHEN** un usuario inicia sesión en el backoffice
- **THEN** el sidebar muestra únicamente las secciones retornadas por el endpoint de navegación para su rol
