## ADDED Requirements

### Requirement: Login con email y password
El sistema SHALL autenticar usuarios mediante email y password. Las contraseñas SHALL almacenarse con hashing bcrypt y nunca en texto plano. Un login exitoso SHALL retornar un access token y un refresh token JWT.

#### Scenario: Login exitoso
- **WHEN** un usuario envía a `POST /api/v1/auth/login` un email y password correctos
- **THEN** el sistema responde `200` con un `access_token` y un `refresh_token`

#### Scenario: Credenciales inválidas
- **WHEN** un usuario envía email o password incorrectos
- **THEN** el sistema responde `401` sin revelar si el email existe

### Requirement: Claims del access token
El access token SHALL incluir los claims `sub` (id de usuario), `tenant_id` y `role`, y una expiración configurable.

#### Scenario: Token contiene contexto de tenant y rol
- **WHEN** se decodifica un access token válido
- **THEN** contiene `sub`, `tenant_id`, `role` y una fecha de expiración

### Requirement: Refresco de token
El sistema SHALL permitir obtener un nuevo access token a partir de un refresh token válido y no expirado.

#### Scenario: Refresco exitoso
- **WHEN** se envía un refresh token válido a `POST /api/v1/auth/refresh`
- **THEN** el sistema responde con un nuevo `access_token`

#### Scenario: Refresh token expirado o inválido
- **WHEN** se envía un refresh token expirado o manipulado
- **THEN** el sistema responde `401`

### Requirement: Usuario autenticado actual
El sistema SHALL exponer `GET /api/v1/auth/me` que retorna los datos del usuario autenticado (id, nombre, email, rol, tenant) a partir del access token.

#### Scenario: Recuperar perfil autenticado
- **WHEN** un usuario con access token válido consulta `GET /api/v1/auth/me`
- **THEN** el sistema responde `200` con su id, nombre, email, rol y tenant

#### Scenario: Sin token
- **WHEN** se consulta `GET /api/v1/auth/me` sin cabecera `Authorization`
- **THEN** el sistema responde `401`
