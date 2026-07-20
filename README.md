# EffiCarBroker

SaaS multitenant de consignación y corretaje automotriz (vertical de **Effi4Tech**).
Primer tenant: *vendemostuautomovil.com*.

Monorepo:

- `backend/` — API FastAPI + PostgreSQL (corre **siempre en Docker**, dentro de un venv aislado).
- `backoffice/` — Panel de administración React 18 + Vite + TS + Tailwind (corre con `npm run dev`).
- `landing/` — Landing pública Next.js, una app por tenant (iteración futura).

Especificación: `SEMILLA_OPENSPEC.md` (funcional), `AGENTS.md` (técnico), `openspec/` (spec-driven).

---

## Requisitos

- Docker Desktop (encendido)
- Node.js 20+ y npm

## 1. Backend (Docker)

```bash
# Desde la raíz del repo
cp .env.example .env            # primera vez
docker compose up -d --build    # levanta PostgreSQL + backend (hot-reload)

# Migración inicial y datos de desarrollo
docker compose exec backend alembic upgrade head
docker compose exec backend python -m src.seed
```

- API: http://localhost:8000/api/v1
- Docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

Para bajar todo (y borrar datos): `docker compose down -v`.

## 2. Backoffice (npm run dev)

```bash
cd backoffice
cp .env.example .env            # primera vez (VITE_API_URL apunta al backend)
npm install                     # primera vez
npm run dev                     # http://localhost:5173
```

## Usuarios de desarrollo (seed)

Password para **todos**: `admin123`.

| Usuario | Email | Rol |
|---|---|---|
| Marcelo Moya | mmoyainfo@gmail.com | SuperAdmin (plataforma) |
| Bastian Galve | bastian@vendemostuautomovil.com | TenantAdmin |
| Josefa Cuevas | josefa@vendemostuautomovil.com | Management |
| Araneth Díaz | araneth@vendemostuautomovil.com | Sales (Santiago) |
| Juan Guillermo Rojas | juanguillermo@vendemostuautomovil.com | Sales (Santiago) |
| Cristian Farías | cristian@vendemostuautomovil.com | Sales (Rancagua) |
| Gabriel Hernández | gabriel@vendemostuautomovil.com | Sales (Rancagua) |

> Pendiente definir rol de Alejandro Debezzi (Marketing) y Matteo Galve (Asistente): fuera del seed hasta acordar rol y accesos.

## Convenciones clave

- **Multitenancy por fila:** toda consulta transaccional filtra por el `tenant_id` del usuario autenticado (derivado del JWT).
- **Todo enum es tabla catálogo** (`roles`, `ciudades`, `estados_vehiculo`, menú): nada hardcodeado. Capas: maestras / catálogos / operacionales.
- **Auditoría append-only:** `logs_auditoria` rechaza `UPDATE`/`DELETE` (trigger PostgreSQL).
- **API versionada** en `/api/v1`. Tipado estricto (Pydantic v2 / TS strict).
