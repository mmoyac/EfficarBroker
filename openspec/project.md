# EffiCarBroker — Contexto de Proyecto

Vertical automotriz del SaaS de consignación y corretaje de **Effi4Tech**. Cliente inicial (primer tenant): *vendemostuautomovil.com*. Plataforma multitenant que gestiona el ciclo completo de corretaje de vehículos: tasación, recepción/consignación virtual, publicación, agendamiento de visitas, liquidación de comisiones y auditoría.

## Stack Tecnológico

### Backend API (Core)
- **Framework:** FastAPI (Python 3.11+)
- **Base de Datos:** PostgreSQL 15+ — aislamiento multitenant por fila (`tenant_id` en toda tabla transaccional)
- **ORM / Migraciones:** SQLAlchemy 2.x + Alembic
- **Validación:** Pydantic v2 (modo estricto)
- **Auth:** JWT (access + refresh)
- **Ejecución:** SIEMPRE en Docker (dev, staging, prod)

### Backoffice (Panel Admin)
- React 18 + Vite + TypeScript (strict mode)
- Tailwind CSS
- TanStack Query (React Query) + Axios, Context API para auth/RBAC
- Sidebar dinámico según rol vía `GET /api/v1/navigation/menu`
- **Ejecución en dev:** `npm run dev` (fuera de Docker)

### Identidad Visual (replica de vendemostuautomovil.com)
- **Accent / marca:** `#FFD701` (amarillo dorado) — botones primarios, destacados; texto negro encima
- **Dark / superficie:** `#222732` (azul-gris oscuro) — sidebar, headers
- **Texto principal:** `#1f2124`; **dark profundo:** `#0f141e` / `#2f3b48`
- **Fondos claros:** `#f2f5fb` / `#e7edf3` / `#ffffff`; **texto atenuado:** `#99a1b2` / `#69727d`
- Se materializa en `tailwind.config.js` del backoffice

### Landing Pública (Catálogo)
- Next.js 14+ (App Router), SSR/SSG para SEO, Tailwind CSS
- **Una app Next.js por tenant (carpeta por landing):** `landing/<tenant>/` con diseño y branding propio de cada tenant. Todas consumen el MISMO backend multitenant vía API pública, resolviendo el `tenant_id` por dominio.
- Primera landing: `landing/vendemostuautomovil/`.
- Cuando exista un 2º tenant, extraer lo común (cliente API, tipos, componentes base) a un paquete compartido; no antes.
- *(Se incorpora tras tener catálogo publicable — depende de M1–M3)*

### Orquestación
- n8n vía webhooks (aprobación de contratos, notificaciones email/WhatsApp)
- *(Se incorpora en una iteración posterior)*

## Estructura de Directorios (monorepo)

```
efficarbroker-platform/
├── docker-compose.yml
├── backend/          # FastAPI (Docker)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── src/{main.py, config/, database.py, models/, schemas/, routers/, services/, utils/}
├── backoffice/       # React + Vite + TS (npm run dev en dev)
│   └── src/{main.tsx, App.tsx, components/, context/, hooks/, pages/, services/, types/}
├── landing/          # Una app Next.js por tenant (futuro)
│   └── vendemostuautomovil/   # primera landing
└── n8n/workflows/    # Flujos automatizados (futuro)
```

## Roles (tabla MAESTRA, administrable por SuperAdmin, global)
`roles` es una **maestra** administrable: el SuperAdmin puede crear/editar roles y asignar a cada uno sus opciones de menú (globales para todos los tenants). Relación: `users.role_id → roles`, y `roles ⇄ menu_items` vía la tabla puente `rol_menu_item`. Vienen precargados por seed reflejando los cargos reales de vendemostuautomovil.com/nosotros:
- `SuperAdmin` — dueño global del SaaS (rol de plataforma/sistema)
- `TenantAdmin` — CEO / Founder de la automotora (Bastian Galve); Estado de Resultados
- `Management` — administración/operaciones (Josefa Cuevas); aprueba paso a `PUBLICADO`
- `Sales` — ejecutivos captación/venta (Araneth, Juan Guillermo, Cristian, Gabriel); acceso a sus sucursales
- `Marketing` — equipo de marketing (Alejandro Debezzi); menú a definir por el SuperAdmin
- `AdministrativeAssistant` — asistente administrativo (Matteo Galve); menú a definir por el SuperAdmin
- `Client` — propietario del auto (externo); ve solo su vehículo

## Estados del Vehículo (ciclo de vida)
`PROSPECTO` → `RECEPCIONADO` → `CONTRATO_ACEPTADO` → `PUBLICADO` (± `CON_VISITA_PROGRAMADA`) → `VENDIDO`

## Convenciones y Restricciones Duras
- **Todo enum es tabla catálogo — nada hardcodeado:** cualquier atributo enumerado (estados, tipos, roles, ciudades, categorías, ítems de menú, tasas configurables, etc.) DEBE modelarse como tabla catálogo referenciada por FK y seedearse. Prohibido dejar valores de dominio como literales en código o strings libres. El esquema se organiza en tres capas:
  - **Maestras:** entidades núcleo, algunas administrables (`tenants`, `users`, `sucursales`, `roles` — administrable por SuperAdmin con su mapeo de menús).
  - **Catálogos:** valores enumerados (`ciudades`, `estados_vehiculo`, `menu_secciones`, `menu_items`, …).
  - **Operacionales:** transaccionales (`logs_auditoria`, y a futuro vehículos, contratos, visitas, liquidaciones).
  - Excepción: en auditoría append-only, `estado_anterior`/`estado_nuevo` se guardan como snapshot de texto inmutable (además del catálogo referencial).
- **Multitenancy no negociable:** ninguna query (SELECT/UPDATE/DELETE) se ejecuta sin filtrar por el `tenant_id` del usuario autenticado. Los datos de un tenant jamás se mezclan con otro.
- **Auditoría append-only:** cada mutación sobre un vehículo inserta una fila inmutable en `logs_auditoria`. Prohibido `UPDATE`/`DELETE` sobre esa tabla. Campos mandatorios: `tenant_id`, usuario, timestamp servidor, IP, estado anterior, estado nuevo, payload JSON.
- **API versionada:** prefijo `/api/v1/`.
- **Moneda:** pesos chilenos (CLP), montos enteros. UF donde la regla de negocio lo indique.
- **Tipado estricto:** Pydantic strict en backend, TS strict en frontend.
- Docs de negocio de referencia: `SEMILLA_OPENSPEC.md` (funcional) y `AGENTS.md` (técnico).

## Módulos (roadmap)
- **M0 — Core SaaS:** infra Docker, Auth JWT, multitenancy, RBAC, auditoría, navegación por rol *(EN CURSO — primer entregable)*
- M1 — Tasación e inteligencia de mercado (scraping Chileautos)
- M2 — Inspección y formalización (acta de recepción, consignación virtual)
- M3 — Validación y publicación (catálogo)
- M4 — Agendamiento de visitas
- M5 — Liquidación, comisiones cruzadas y Estado de Resultados
- M6 — Auditoría (registro inmutable)
- M7 — Menús dinámicos del Backoffice por rol
