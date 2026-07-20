## ADDED Requirements

### Requirement: Modelo de Tenant
El sistema SHALL modelar cada automotora cliente como un `tenant` con identificador único, nombre y dominio. Toda tabla transaccional (usuarios, sucursales, vehículos, contratos, liquidaciones, auditoría) SHALL poseer una llave foránea `tenant_id`.

#### Scenario: Tenant persistido
- **WHEN** se crea el tenant `vendemostuautomovil.com`
- **THEN** se registra con un `tenant_id` único y las tablas transaccionales referencian ese `tenant_id`

### Requirement: Aislamiento por fila obligatorio
Ninguna consulta transaccional (SELECT, UPDATE, DELETE) SHALL ejecutarse sin filtrar por el `tenant_id` del usuario autenticado. Los datos de un tenant NO SHALL ser accesibles desde el contexto de otro tenant.

#### Scenario: Usuario solo ve datos de su tenant
- **WHEN** un usuario autenticado del tenant A solicita un recurso transaccional
- **THEN** la respuesta contiene únicamente registros cuyo `tenant_id` coincide con el del usuario

#### Scenario: Acceso cruzado entre tenants bloqueado
- **WHEN** un usuario del tenant A solicita por id un recurso que pertenece al tenant B
- **THEN** el sistema responde como no encontrado (`404`) y no revela datos del tenant B

### Requirement: Contexto de tenant derivado del token
El `tenant_id` SHALL derivarse del claim del JWT del usuario autenticado y exponerse como contexto de la petición, no como parámetro manipulable por el cliente.

#### Scenario: tenant_id no manipulable por el cliente
- **WHEN** el cliente intenta enviar un `tenant_id` distinto en el cuerpo o query de la petición
- **THEN** el sistema ignora ese valor y usa exclusivamente el `tenant_id` del token

#### Scenario: SuperAdmin transversal
- **WHEN** un usuario con rol `SuperAdmin` accede a recursos de plataforma
- **THEN** el filtrado obligatorio por un único `tenant_id` no aplica y puede operar a nivel multi-tenant
