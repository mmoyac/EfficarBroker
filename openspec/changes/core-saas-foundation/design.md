## Context

Es el primer cambio del proyecto EffiCarBroker: no existe código. El objetivo es levantar la base ejecutable multitenant sobre la que se construirán los módulos de negocio 1–7. El backend debe correr siempre en Docker junto a PostgreSQL; el backoffice se ejecuta en desarrollo con `npm run dev` apuntando al backend contenedorizado. El aislamiento por `tenant_id` y la auditoría append-only son restricciones duras de la especificación funcional (SEMILLA_OPENSPEC.md, Módulos 0 y 6).

## Goals / Non-Goals

**Goals:**
- `docker-compose` que levante backend + PostgreSQL 15 con un solo comando y hot-reload en dev.
- Esqueleto FastAPI estructurado por dominios, migraciones Alembic y healthcheck.
- Modelo de datos base multitenant (`tenants`, `roles`, `users`, `sucursales`, `logs_auditoria`).
- Auth JWT (access/refresh) con RBAC de 5 roles y guards reutilizables.
- Mecanismo de aislamiento por `tenant_id` derivado del token, difícil de saltar por olvido del desarrollador.
- Auditoría append-only reutilizable por los módulos futuros.
- Endpoint de navegación por rol y backoffice con login + sidebar dinámico.
- Seed de datos de desarrollo (tenant vendemostuautomovil.com + usuarios por rol).

**Non-Goals:**
- Landing pública Next.js y flujos n8n (iteraciones posteriores).
- Lógica de negocio de tasación, recepción, publicación, visitas o liquidación.
- Multi-tenant por subdominio/header (se difiere; ahora el tenant se deriva del usuario).
- Row-Level Security nativo de PostgreSQL (se evalúa a futuro; ahora se aplica en capa de aplicación).
- CI/CD, staging y despliegue productivo.

## Decisions

### D1 — Tenant derivado del JWT + BaseModel con `tenant_id`
El `tenant_id` se embebe como claim del access token al hacer login y se expone vía dependency `get_current_tenant()`. Toda tabla transaccional hereda de una `TenantBaseModel` (mixin con columna `tenant_id` indexada, FK a `tenants`). Las consultas se hacen a través de un helper/repositorio que aplica `.filter(Model.tenant_id == ctx.tenant_id)` de forma centralizada.
- *Alternativa considerada:* PostgreSQL RLS con `SET app.current_tenant`. Más robusto pero añade complejidad operacional (roles de BD, políticas) que no aporta en dev inicial. Se deja la puerta abierta migrando cuando el modelo esté estable.
- *Por qué:* balance entre seguridad y velocidad; el mixin + helper hace el filtrado el camino por defecto y el olvido la excepción visible.

### D2 — RBAC por rol único con guards de FastAPI
Cada usuario tiene un `role_id` (rol único, no lista de permisos granulares por ahora). Se implementa `require_roles(*roles)` como dependency que valida el claim `role` del token. `SuperAdmin` es transversal a tenants (no filtra por `tenant_id`); el resto opera dentro de su tenant.
- *Alternativa:* permisos granulares (tabla `permissions` + `role_permissions`). Sobre-ingeniería para M0; la matriz de roles de la spec es suficiente con rol único. Se puede extender luego sin romper el contrato.

### D3 — Auth con JWT access + refresh
Access token corto (ej. 30 min) con claims `sub` (user_id), `tenant_id`, `role`. Refresh token largo (ej. 7 días) para renovar. Passwords con bcrypt (passlib). Librería `pyjwt`.
- *Por qué access+refresh:* estándar, permite sesiones largas en backoffice sin exponer credenciales; refresh revocable a futuro.

### D4 — Auditoría append-only como servicio + constraint
`logs_auditoria` es append-only. Se ofrece `audit_service.log(...)` que inserta una fila con `tenant_id`, `user_id`, `timestamp` (servidor), `ip`, `estado_anterior`, `estado_nuevo`, `payload` (JSONB). Se protege con un trigger de PostgreSQL que lanza excepción ante `UPDATE`/`DELETE`, además de no exponer operaciones de mutación en la capa de app.
- *Por qué trigger + disciplina de app:* defensa en profundidad; la spec prohíbe explícitamente UPDATE/DELETE.

### D5 — Menú de navegación en tablas catálogo (no hardcodeado)
`GET /api/v1/navigation/menu` construye el árbol consultando tablas catálogo `menu_secciones` y `menu_items` (etiqueta, icono, ruta, orden, sección padre) mapeadas a rol vía `rol_menu_item` (o columna `role_id` en el ítem). Retorna solo lo permitido para el rol del token, tomando la estructura de SEMILLA_OPENSPEC.md Módulo 7. La definición se seedea; el frontend no hardcodea menús.
- *Por qué en BD:* cumple la regla dura del proyecto (todo enum/estructura de dominio es catálogo, nada hardcodeado) y habilita personalización por rol/tenant sin recompilar.
- *Alternativa descartada:* definición declarativa en código backend — viola la convención de catálogos.

### D6 — Backoffice: Vite + TanStack Query + Context de Auth
Contexto de auth guarda el token (en memoria + refresh en almacenamiento) y expone user/rol. Axios con interceptor que adjunta `Authorization: Bearer` y refresca ante 401. El Sidebar se pinta consumiendo `/navigation/menu` vía React Query. Rutas protegidas por rol en el cliente (además del guard del backend).

### D8 — Modelado en capas con catálogos (todo enum es tabla)
El esquema se organiza en **maestras** (`tenants`, `users`, `sucursales`), **catálogos** (`roles`, `ciudades`, `estados_vehiculo`, `menu_secciones`, `menu_items`) y **operacionales** (`logs_auditoria`). Todo atributo enumerado se modela como catálogo referenciado por FK y se seedea; ningún valor de dominio queda hardcodeado en código ni como string libre. En M0 esto implica: `roles` (catálogo), `ciudades` (catálogo, referenciado por `sucursales.ciudad_id`), `estados_vehiculo` (catálogo fundacional que usarán M1+), y el menú en catálogos.
- *Por qué:* regla dura del proyecto; modelo parametrizable/mantenible sin recompilar.
- *Excepción:* `logs_auditoria.estado_anterior`/`estado_nuevo` se guardan como snapshot de texto inmutable (patrón de auditoría), además de existir el catálogo `estados_vehiculo` para referencia.

### D7 — Config por variables de entorno
`.env` para credenciales de BD, `JWT_SECRET`, `JWT_EXPIRE`, CORS origins. Pydantic `BaseSettings`. El backoffice usa `VITE_API_URL`.

## Risks / Trade-offs

- **Olvido de filtrar por `tenant_id` en una query nueva** → Mitigación: mixin `TenantBaseModel` + helper de repositorio como camino por defecto; revisión en code-review; a futuro migrar a RLS.
- **Filtrado en capa de app (no RLS)** deja margen a fugas si alguien usa la sesión cruda → Mitigación: encapsular acceso a datos; test de aislamiento entre dos tenants como parte de las tareas.
- **Trigger append-only puede complicar migraciones/seeds** → Mitigación: seed inserta solo vía INSERT; el trigger bloquea únicamente UPDATE/DELETE.
- **Rol único vs permisos granulares** puede quedar corto para reglas finas (ej. Sales limitado a sus sucursales) → Mitigación: para M0 basta el filtro por rol + tenant; el filtro por sucursal se añade en los módulos que lo requieran.
- **Secret JWT en `.env` de dev** → Mitigación: `.env` en `.gitignore`, `.env.example` versionado; secretos reales solo en staging/prod.

## Migration Plan

1. Crear estructura monorepo y `docker-compose.yml`.
2. `docker compose up` levanta PostgreSQL + backend; Alembic aplica migración inicial.
3. Ejecutar seed (comando/script) para tenant, roles y usuarios de ejemplo.
4. `npm install && npm run dev` en `backoffice/` apuntando al backend.
5. Rollback: `docker compose down -v` elimina contenedores y volumen; sin datos productivos aún.

## Open Questions

- ¿Tiempos exactos de expiración de tokens (access/refresh)? — Se asumen 30 min / 7 días, ajustables por `.env`.
- ¿Se persiste blacklist de refresh tokens para logout server-side? — Se difiere a un cambio posterior; por ahora logout es client-side.
- ¿El `SuperAdmin` vive dentro de un tenant "plataforma" o fuera de todo tenant? — Se asume `tenant_id` nullable solo para SuperAdmin.
- **Rol de Alejandro Debezzi (Marketing) y Matteo Galve (Administrative Assistant):** sus cargos no calzan con la matriz RBAC de 5 roles. Quedan FUERA del seed por ahora (decisión del usuario). Antes de incluirlos, definir con el usuario: (a) qué rol tendrán —reutilizar `Sales`/`Management` o crear un rol nuevo (ej. `Marketing`)— y (b) a qué opciones/secciones de menú podrán acceder.
