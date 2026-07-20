## 1. Backend — token y contexto

- [x] 1.1 `create_access_token` acepta `active_tenant_id` opcional y lo incluye como claim cuando está presente
- [x] 1.2 Extender `TenantContext` con `active_tenant_id` y resolver el tenant efectivo en `get_current_tenant` (no-SA: tenant propio; SA: active_tenant_id o None)

## 2. Backend — endpoints

- [x] 2.1 `GET /api/v1/tenants` (solo SuperAdmin) que lista tenants (id, nombre, dominio, activo)
- [x] 2.2 `POST /api/v1/auth/select-tenant` (solo SuperAdmin): valida tenant existente y activo, re-emite access token con `active_tenant_id` (404/400 en inválidos)
- [x] 2.3 `POST /api/v1/auth/exit-tenant` (solo SuperAdmin): re-emite access token sin `active_tenant_id`
- [x] 2.4 `/auth/me` expone `active_tenant_id` y `active_tenant` (nombre) cuando aplica

## 3. Backoffice — contexto y UI

- [x] 3.1 Extender el contexto de auth: exponer tenant activo, `selectTenant(id)` y `exitTenant()` que guardan el token re-emitido e invalidan queries de me/menu
- [x] 3.2 Vista de plataforma (directorio de tenants) que se muestra al SuperAdmin sin tenant activo
- [x] 3.3 Switcher de tenant en el layout (visible solo para SuperAdmin): muestra tenant activo, permite cambiar y volver a plataforma
- [x] 3.4 Enrutamiento: SuperAdmin sin tenant activo aterriza en la vista de plataforma; con tenant activo, en el dashboard operativo

## 4. Verificación

- [x] 4.1 Seed: crear un 2º tenant de demo para probar el cambio de contexto
- [x] 4.2 Probar: SuperAdmin lista tenants → selecciona → /me refleja tenant activo → exit vuelve a plataforma; no-SuperAdmin recibe 403 en los endpoints de tenant
