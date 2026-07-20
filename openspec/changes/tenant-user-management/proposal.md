## Why

Un tenant necesita administrar a su propio equipo: dar de alta a los ejecutivos, asignarles rol y sucursal, editarlos, desactivarlos y resetear su contraseña. Hoy los usuarios solo existen vía seed. Esta es la opción "Gestión de Usuarios" del Módulo 7, disponible para el TenantAdmin y para el SuperAdmin cuando opera dentro de un tenant. Además, siendo un SaaS, cada tenant tiene un **cupo de usuarios licenciado** (una cantidad comprada o ilimitado) que solo el SuperAdmin puede definir, y que se valida al crear usuarios.

## What Changes

- **CRUD de usuarios del tenant** (solo `TenantAdmin` y `SuperAdmin`), siempre scopeado al **tenant efectivo**:
  - `GET /api/v1/users` — lista los usuarios del tenant efectivo.
  - `POST /api/v1/users` — crea un usuario (nombre, email, rol, sucursal opcional, teléfono); password inicial `admin123` (dev).
  - `GET /api/v1/users/{id}` — detalle (dentro del tenant).
  - `PATCH /api/v1/users/{id}` — edita nombre, teléfono, rol, sucursal y estado activo.
  - `POST /api/v1/users/{id}/reset-password` — resetea la contraseña a `admin123` (dev).
- **Catálogos de apoyo para el formulario:**
  - `GET /api/v1/roles` — roles asignables (excluye `SuperAdmin`).
  - `GET /api/v1/sucursales` — sucursales del tenant efectivo.
- **Licenciamiento de usuarios por tenant (SaaS):**
  - Nueva columna `tenants.max_usuarios` (`NULL` = ilimitado; entero = cupo comprado).
  - `PATCH /api/v1/tenants/{id}` (solo `SuperAdmin`) para fijar/editar el cupo.
  - `GET /api/v1/tenants` incluye `max_usuarios` y el conteo actual de usuarios (uso, ej. 3/10).
  - Al crear o reactivar un usuario, se valida el cupo de usuarios **activos**; si se alcanzó el límite, se responde `409` con mensaje claro. El `TenantAdmin` NO puede modificar su propio cupo.
- **Reglas:** email único por tenant (409 si repetido); no se puede asignar el rol `SuperAdmin`; no se puede desactivar la propia cuenta; imposible ver/editar usuarios de otro tenant; si el SuperAdmin no tiene tenant activo, estos endpoints exigen seleccionar uno primero.
- **Backoffice:** página "Gestión de Usuarios" (`/config/usuarios`) con tabla de usuarios, crear/editar en formulario, activar/desactivar y resetear contraseña; indicador de cupo (usados/límite). En el directorio de tenants (SuperAdmin), edición del cupo por tenant.

## Capabilities

### New Capabilities
- `user-management`: Gestión (CRUD) de los usuarios de un tenant por parte del TenantAdmin/SuperAdmin, scopeada al tenant efectivo, con asignación de rol y sucursal.
- `tenant-licensing`: Cupo de usuarios por tenant fijado por el SuperAdmin (cantidad o ilimitado) y validado al crear/reactivar usuarios.

### Modified Capabilities
<!-- Ninguna delta sobre specs archivadas: capacidades nuevas. -->

## Impact

- **APIs nuevas:** `/users` (CRUD), `/users/{id}/reset-password`, `/roles`, `/sucursales`, `PATCH /tenants/{id}`.
- **Base de datos:** columna `tenants.max_usuarios` (migración 0002).
- **Backend:** router de usuarios con scoping por tenant efectivo (primer uso real del filtro por `tenant_id`), validación de cupo, schemas Pydantic, manejo de email duplicado.
- **Backoffice:** página de gestión de usuarios + edición de cupo del tenant + hooks de datos.
- Primer módulo de datos transaccionales que ejercita el aislamiento multitenant y el licenciamiento SaaS end-to-end.
