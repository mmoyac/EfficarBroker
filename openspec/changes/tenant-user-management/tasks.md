## 1. Backend — licenciamiento (cupo)

- [x] 1.1 Añadir columna `max_usuarios` (nullable) al modelo `Tenant` y migración Alembic 0002
- [x] 1.2 `PATCH /api/v1/tenants/{id}` (solo SuperAdmin) para fijar `max_usuarios` (entero o null)
- [x] 1.3 `GET /api/v1/tenants` incluye `max_usuarios` y `usuarios_activos` (conteo); `GET /tenants/current` para el TenantAdmin
- [x] 1.4 Helper de validación de cupo: cuenta usuarios activos del tenant y bloquea (409) si se alcanzó el límite

## 2. Backend — CRUD de usuarios (scopeado al tenant efectivo)

- [x] 2.1 Schemas `UserCreate`, `UserUpdate`, `UserOut`, `RoleOut`, `SucursalOut`
- [x] 2.2 Router `users` con `require_roles("TenantAdmin")`; `get_effective_tenant_id` exige tenant efectivo (409 si SuperAdmin sin tenant activo)
- [x] 2.3 `GET /api/v1/users` (lista del tenant efectivo) y `GET /api/v1/users/{id}` (404 si es de otro tenant)
- [x] 2.4 `POST /api/v1/users` (password inicial `admin123`, valida cupo, email único → 409, rol SuperAdmin → 400)
- [x] 2.5 `PATCH /api/v1/users/{id}` (nombre, teléfono, rol, sucursal, activo; no auto-desactivar; reactivar valida cupo)
- [x] 2.6 `POST /api/v1/users/{id}/reset-password` (resetea a `admin123`)
- [x] 2.7 `GET /api/v1/roles` (asignables, sin SuperAdmin) y `GET /api/v1/sucursales` (del tenant efectivo)

## 3. Backoffice — Gestión de Usuarios

- [x] 3.1 Servicios/hooks: listar/crear/editar/reset usuarios, listar roles y sucursales, tenant actual y editar cupo
- [x] 3.2 Página `/config/usuarios`: tabla de usuarios (nombre, email, rol, sucursal, estado) con indicador de cupo usados/límite
- [x] 3.3 Formulario crear/editar usuario (rol y sucursal desde catálogo) + acciones activar/desactivar y resetear contraseña
- [x] 3.4 SuperAdmin: edición del cupo (`max_usuarios`) del tenant, con opción "ilimitado"

## 4. Verificación

- [x] 4.1 Fijar cupo del tenant demo, crear usuarios hasta el tope y verificar `409` al exceder; desactivar libera cupo
- [x] 4.2 Verificar aislamiento: usuarios de un tenant no visibles desde otro (404); email único por tenant (409); rol SuperAdmin no asignable (400); TenantAdmin no puede editar cupo (403); SuperAdmin sin tenant activo (409)
