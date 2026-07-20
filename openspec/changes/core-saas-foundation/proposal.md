## Why

EffiCarBroker es un SaaS multitenant donde cada módulo de negocio (tasación, recepción, publicación, liquidación) depende de un usuario autenticado, asociado a un `tenant_id` y con un rol RBAC. Sin esta base fundacional no es posible construir ningún flujo de negocio de forma segura ni aislar los datos entre automotoras. Este cambio entrega la plataforma mínima ejecutable (backend en Docker + backoffice React) sobre la que se implementarán los módulos 1 a 7.

## What Changes

- **Infraestructura Docker local:** `docker-compose.yml` que levanta backend (FastAPI) y PostgreSQL 15. El backend siempre corre en Docker; el backoffice corre con `npm run dev`.
- **Esqueleto Backend:** proyecto FastAPI con estructura por dominios (`config/`, `database.py`, `models/`, `schemas/`, `routers/`, `services/`, `utils/`), Alembic para migraciones y healthcheck `GET /api/v1/health`.
- **Modelo de datos base:** tablas `tenants`, `roles`, `users`, `sucursales`, `logs_auditoria`, todas con `tenant_id` (salvo `tenants`) y timestamps.
- **Autenticación JWT:** login con email + password, tokens access/refresh, endpoint `GET /api/v1/auth/me`, hashing con bcrypt.
- **Multitenancy por fila:** el `tenant_id` se deriva del usuario autenticado y se inyecta como contexto obligatorio en toda consulta transaccional; imposible consultar datos de otro tenant.
- **RBAC:** 5 roles (`SuperAdmin`, `TenantAdmin`, `Management`, `Sales`, `Client`) con dependencias/guards de FastAPI para proteger endpoints por rol.
- **Auditoría append-only:** utilidad/interceptor que registra mutaciones en `logs_auditoria`; prohibido `UPDATE`/`DELETE` sobre esa tabla.
- **Navegación dinámica:** `GET /api/v1/navigation/menu` que retorna el árbol de menú del sidebar según el rol del usuario.
- **Seed inicial:** tenant `vendemostuautomovil.com`, roles y usuarios de ejemplo por rol para desarrollo.
- **Esqueleto Backoffice:** React 18 + Vite + TS (strict) + Tailwind, con pantalla de Login, contexto de auth/RBAC, cliente Axios con interceptor de token, TanStack Query, y Sidebar renderizado desde el endpoint de navegación.

## Capabilities

### New Capabilities
- `platform-infrastructure`: Orquestación Docker local, esqueleto de backend FastAPI con Alembic, esqueleto de backoffice React, y seed de datos de desarrollo.
- `multitenancy`: Modelo de tenant y aislamiento por fila; el `tenant_id` del usuario autenticado filtra obligatoriamente toda consulta transaccional.
- `authentication`: Login por email/password, emisión y refresco de JWT (access/refresh) y recuperación del usuario autenticado.
- `rbac`: Definición de los 5 roles, asignación a usuarios y guards de autorización por rol sobre los endpoints.
- `audit-log`: Registro inmutable append-only de mutaciones con `tenant_id`, usuario, timestamp, IP, estado anterior/nuevo y payload JSON.
- `navigation-menu`: Endpoint que entrega el árbol de menú del backoffice filtrado por rol y tenant del usuario.

### Modified Capabilities
<!-- Ninguna: es el primer cambio del proyecto. -->

## Impact

- **Código nuevo:** repositorio monorepo (`backend/`, `backoffice/`, `docker-compose.yml`), migraciones Alembic iniciales.
- **APIs nuevas:** `/api/v1/health`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/me`, `/api/v1/navigation/menu`.
- **Dependencias:** FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, psycopg, python-jose/pyjwt, passlib/bcrypt (backend); React 18, Vite, TanStack Query, Axios, Tailwind (backoffice).
- **Base de datos:** PostgreSQL 15 en contenedor; esquema base multitenant.
- **Sienta las bases** de seguridad, aislamiento y navegación para los módulos 1–7. No incluye landing Next.js ni n8n (iteraciones futuras).
