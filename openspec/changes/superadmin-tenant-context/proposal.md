## Why

El SaaS puede alojar múltiples automotoras (tenants). Hoy el SuperAdmin es transversal pero no tiene forma de "entrar" a operar dentro de un tenant concreto: no hay selección de tenant activo. Se necesita que el SuperAdmin, tras autenticarse, vea la plataforma y pueda seleccionar con qué tenant trabajar, quedando su contexto scopeado a ese tenant de forma segura y auditable.

## What Changes

- **Listado de tenants:** `GET /api/v1/tenants` (solo SuperAdmin) para elegir con cuál trabajar.
- **Selección de tenant activo:** `POST /api/v1/auth/select-tenant` (solo SuperAdmin) re-emite un access token con el claim `active_tenant_id`. El contexto de tenant sigue derivándose del token (no manipulable por el cliente).
- **Salir a vista plataforma:** `POST /api/v1/auth/exit-tenant` re-emite un token sin `active_tenant_id`.
- **Contexto efectivo:** `get_current_tenant` resuelve el tenant efectivo — para SuperAdmin es el `active_tenant_id` seleccionado (o ninguno en vista plataforma); para el resto, su tenant propio.
- **`/auth/me`** expone el tenant activo para que el frontend muestre el contexto.
- **Backoffice:** pantalla/selector de tenant para SuperAdmin tras el login (vista plataforma), switcher para cambiar de tenant o volver a plataforma, y contexto de auth que gestiona el tenant activo.

## Capabilities

### New Capabilities
- `tenant-context`: Selección de un tenant activo por parte del SuperAdmin mediante re-emisión de token (claim `active_tenant_id`), resolución del tenant efectivo, exposición del tenant activo en `/auth/me`, y vista de plataforma vs. operación dentro de un tenant.

### Modified Capabilities
<!-- Las capacidades authentication y multitenancy del Módulo 0 aún no están archivadas en openspec/specs/; sus ajustes (claim active_tenant_id, tenant efectivo) se consolidan en la nueva capacidad tenant-context. -->

## Impact

- **APIs nuevas:** `GET /api/v1/tenants`, `POST /api/v1/auth/select-tenant`, `POST /api/v1/auth/exit-tenant`.
- **Backend:** `create_access_token` acepta `active_tenant_id`; `TenantContext` y `get_current_tenant` resuelven tenant efectivo; guard SuperAdmin.
- **Backoffice:** vista de plataforma con directorio de tenants, switcher de tenant en el layout, contexto de auth extendido.
- Base para el aislamiento de datos del SuperAdmin cuando lleguen los endpoints transaccionales (M1+).
