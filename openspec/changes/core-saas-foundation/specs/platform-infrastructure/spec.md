## ADDED Requirements

### Requirement: Orquestación Docker local
El sistema SHALL proveer un `docker-compose.yml` que levante el backend (FastAPI) y PostgreSQL 15 con un único comando. El backend SHALL ejecutarse siempre dentro de un contenedor Docker, con recarga en caliente para desarrollo. El backoffice NO se contenedoriza en desarrollo: se ejecuta con `npm run dev`.

#### Scenario: Levantar el entorno con un comando
- **WHEN** el desarrollador ejecuta `docker compose up` en la raíz del proyecto
- **THEN** se inician los contenedores de backend y PostgreSQL, y el backend queda accesible en el puerto configurado

#### Scenario: Recarga en caliente del backend
- **WHEN** el desarrollador modifica un archivo fuente del backend estando los contenedores arriba
- **THEN** el servidor FastAPI recarga automáticamente sin reconstruir la imagen

### Requirement: Esqueleto de backend FastAPI
El backend SHALL estructurarse por dominios siguiendo `src/{config, database, models, schemas, routers, services, utils}`, usar Alembic para migraciones y exponer un healthcheck.

#### Scenario: Healthcheck responde
- **WHEN** se hace `GET /api/v1/health`
- **THEN** el backend responde `200` con un cuerpo que indica estado `ok` y conectividad con la base de datos

#### Scenario: Migración inicial aplica el esquema base en capas
- **WHEN** se ejecuta la migración inicial de Alembic sobre una base vacía
- **THEN** se crean las tablas maestras (`tenants`, `users`, `sucursales`), las tablas catálogo (`roles`, `ciudades`, `estados_vehiculo`, `menu_secciones`, `menu_items`) y las operacionales (`logs_auditoria`), con las FK correspondientes

### Requirement: Atributos enumerados en tablas catálogo
Todo atributo enumerado del sistema SHALL modelarse como una tabla catálogo referenciada por llave foránea; ningún valor de dominio SHALL quedar hardcodeado en código ni almacenado como string libre. El esquema SHALL organizarse en capas: maestras, catálogos y operacionales.

#### Scenario: Ciudad de sucursal referencia catálogo
- **WHEN** se inspecciona la tabla `sucursales`
- **THEN** la ciudad se referencia mediante FK a la tabla catálogo `ciudades` y no como texto libre

#### Scenario: Rol de usuario referencia catálogo
- **WHEN** se inspecciona la tabla `users`
- **THEN** el rol se referencia mediante FK a la tabla catálogo `roles` y no como texto libre

### Requirement: Esqueleto de backoffice React
El backoffice SHALL ser un proyecto React 18 + Vite + TypeScript en modo estricto, con Tailwind CSS configurado con la paleta de marca, cliente Axios con interceptor de token, y TanStack Query.

#### Scenario: Backoffice arranca en dev
- **WHEN** el desarrollador ejecuta `npm run dev` en `backoffice/`
- **THEN** la aplicación compila sin errores de TypeScript y sirve la pantalla de login apuntando al backend vía `VITE_API_URL`

#### Scenario: Paleta de marca aplicada
- **WHEN** se inspecciona la configuración de Tailwind
- **THEN** existen tokens de color para el accent `#FFD701`, la superficie oscura `#222732` y los fondos claros de marca

### Requirement: Seed de datos de desarrollo
El sistema SHALL proveer un comando/script de seed que poblé las tablas catálogo (`roles`, `ciudades`, `estados_vehiculo`, `menu_secciones`, `menu_items`) y cree el tenant `vendemostuautomovil.com`, las sucursales Santiago y Rancagua, un usuario `SuperAdmin` de plataforma y los usuarios reales del equipo mapeados a sus roles.

#### Scenario: Seed puebla catálogos
- **WHEN** se ejecuta el comando de seed sobre una base migrada
- **THEN** las tablas catálogo `roles`, `ciudades`, `estados_vehiculo`, `menu_secciones` y `menu_items` quedan pobladas con sus valores de dominio

#### Scenario: Seed crea el tenant y usuarios
- **WHEN** se ejecuta el comando de seed sobre una base migrada
- **THEN** existe el tenant `vendemostuautomovil.com` con sus sucursales y usuarios (Bastian Galve como TenantAdmin, Josefa Cuevas como Management, y los ejecutivos como Sales), cada uno referenciando por FK su rol y con contraseña de desarrollo conocida

#### Scenario: Seed es idempotente
- **WHEN** el comando de seed se ejecuta una segunda vez
- **THEN** no se duplican registros ni falla por claves únicas
