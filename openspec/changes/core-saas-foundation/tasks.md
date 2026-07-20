## 1. Andamiaje del monorepo e infraestructura Docker

- [x] 1.1 Crear estructura de carpetas del monorepo (`backend/`, `backoffice/`), `.gitignore`, `README.md` y `.env.example`
- [x] 1.2 Crear `backend/Dockerfile` (Python 3.11-slim, venv aislado) y `backend/requirements.txt` (fastapi, uvicorn, sqlalchemy 2, alembic, psycopg, pydantic v2, pydantic-settings, pyjwt, passlib[bcrypt], python-multipart)
- [x] 1.3 Crear `docker-compose.yml` con servicios `db` (postgres:15, volumen persistente, healthcheck) y `backend` (build local, hot-reload con volumen montado, `depends_on` db healthy, puerto expuesto)
- [x] 1.4 Verificar que `docker compose up` levanta db + backend y el contenedor backend recarga al cambiar un archivo fuente

## 2. Esqueleto backend FastAPI

- [x] 2.1 Crear `src/config/` con settings vía pydantic-settings (DB URL, JWT_SECRET, JWT expiraciones, CORS origins)
- [x] 2.2 Crear `src/database.py` (engine, SessionLocal, `get_db` dependency) y `src/main.py` con app FastAPI, prefijo `/api/v1`, CORS y router de health
- [x] 2.3 Implementar `GET /api/v1/health` que verifica conectividad con la BD
- [x] 2.4 Inicializar Alembic (`alembic.ini`, `migrations/env.py` apuntando al metadata de los modelos)

## 3. Modelos de datos base y migración (capas maestras / catálogos / operacionales)

- [x] 3.1 Crear mixins `TenantMixin` (FK `tenant_id` indexada) y `TimestampMixin` (`created_at`/`updated_at`)
- [x] 3.2 Modelar tablas **catálogo**: `roles`, `ciudades`, `estados_vehiculo`, `menu_secciones`, `menu_items` (etiqueta, icono, ruta, orden, sección padre) y su mapeo a rol (`rol_menu_item`)
- [x] 3.3 Modelar tablas **maestras**: `tenants`; `sucursales` (nombre, dirección, `ciudad_id` FK); `users` (email único por tenant, password_hash, `role_id` FK, `sucursal_id` FK, nombre, teléfono)
- [x] 3.4 Modelar tabla **operacional** `logs_auditoria` (tenant_id, user_id, timestamp, ip, estado_anterior/estado_nuevo como snapshot de texto, payload JSONB)
- [x] 3.5 Generar migración Alembic inicial que crea todas las tablas con sus FK (ningún enum como string libre)
- [x] 3.6 Añadir a la migración un trigger PostgreSQL que rechaza `UPDATE`/`DELETE` sobre `logs_auditoria`

## 4. Autenticación JWT

- [x] 4.1 Utilidades de seguridad: hash/verify de password con bcrypt; crear/decodificar access y refresh tokens (claims `sub`, `tenant_id`, `role`, `exp`)
- [x] 4.2 Schemas Pydantic de login, tokens y usuario; router `POST /api/v1/auth/login` (401 genérico si credenciales inválidas)
- [x] 4.3 `POST /api/v1/auth/refresh` (nuevo access token desde refresh válido; 401 si expirado/inválido)
- [x] 4.4 Dependency `get_current_user` (decodifica token, carga usuario) y `GET /api/v1/auth/me`

## 5. Multitenancy y RBAC

- [x] 5.1 Dependency `get_current_tenant` que expone el `tenant_id` del token como contexto de la petición (ignora cualquier tenant_id enviado por el cliente)
- [ ] 5.2 Helper/repositorio de acceso a datos que aplica el filtro `tenant_id` por defecto en las consultas transaccionales — DIFERIDO: se implementará al aparecer los primeros endpoints transaccionales (M1+). En M0 no hay consultas transaccionales de listado.
- [x] 5.3 Dependency `require_roles(*roles)` que valida el claim `role` y responde 403 si no autorizado; `SuperAdmin` transversal (sin filtro de tenant único)
- [ ] 5.4 Test de aislamiento: dos tenants distintos no acceden a los datos del otro (404 en acceso cruzado por id) — DIFERIDO: requiere un 2º tenant y una suite de tests; el mecanismo (`get_current_tenant` + filtro) ya está en su lugar.

## 6. Auditoría append-only

- [x] 6.1 `audit_service.log(...)` que inserta en `logs_auditoria` con tenant_id, user_id, timestamp servidor, IP (desde request), estado anterior/nuevo y payload JSON
- [x] 6.2 Verificar a nivel de app y de BD que `UPDATE`/`DELETE` sobre `logs_auditoria` fallan (trigger probado: BLOQUEADO)

## 7. Navegación dinámica por rol (desde catálogo)

- [x] 7.1 `GET /api/v1/navigation/menu` autenticado que construye el árbol consultando las tablas catálogo de menú (`menu_secciones`/`menu_items` + mapeo por rol), filtrado por el rol del token (401 sin token); sin menús hardcodeados
- [x] 7.2 Verificar que cada rol recibe solo sus secciones según lo seedeado en las tablas de menú (Sales / Management / TenantAdmin / SuperAdmin verificados)

## 8. Seed de datos de desarrollo

- [x] 8.1 Poblar catálogos: `roles` (5), `ciudades` (Santiago, Rancagua), `estados_vehiculo` (PROSPECTO→RECEPCIONADO→CONTRATO_ACEPTADO→PUBLICADO→VENDIDO), y `menu_secciones`/`menu_items` por rol según SEMILLA_OPENSPEC Módulo 7
- [x] 8.2 Seed maestro idempotente: tenant `vendemostuautomovil.com`, sucursales Santiago y Rancagua (con `ciudad_id`)
- [x] 8.3 Crear usuarios reales del equipo con `role_id` FK (Bastian Galve→TenantAdmin, Josefa Cuevas→Management, Araneth/Juan Guillermo/Cristian/Gabriel→Sales) + el SuperAdmin de plataforma **Marcelo Moya** (mmoyainfo@gmail.com), todos con password de desarrollo `admin123`. PENDIENTE (fuera del seed por ahora): Alejandro Debezzi (Marketing) y Matteo Galve (Administrative Assistant) — definir rol y accesos antes de incluirlos.

## 9. Esqueleto backoffice React

- [x] 9.1 Inicializar proyecto Vite React+TS (strict), Tailwind con tokens de marca (accent `#FFD701`, dark `#222732`, fondos claros), `.env` con `VITE_API_URL`
- [x] 9.2 Configurar Axios con interceptor de token + refresh ante 401, y TanStack Query provider
- [x] 9.3 Context de autenticación (guarda tokens, expone user/rol), pantalla de Login funcional contra `POST /api/v1/auth/login`
- [x] 9.4 Layout con Sidebar que consume `GET /api/v1/navigation/menu` (sin menús hardcodeados) y rutas protegidas en el cliente

## 10. Verificación end-to-end

- [x] 10.1 Documentar en `README.md` los comandos de arranque (backend en Docker, `npm run dev` del backoffice, seed)
- [x] 10.2 Probar el flujo completo: login como cada rol → menú correcto por rol → `/auth/me` refleja rol y tenant (verificado vía API + CORS desde origin 5173)
