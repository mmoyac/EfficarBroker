## Context

EffiCarBroker es un monorepo con `backend/` (FastAPI, módulo `src.main:app`), `backoffice/` (React + Vite) y a futuro `landing/`. Hoy solo existe `docker-compose.yml` de desarrollo (hot-reload, servicio DB llamado `db`, usuario `efficar`, base `efficarbroker`, media en volumen montado en `/app/media` y servido bajo `/media`). Las migraciones ya usan Alembic (`backend/migrations`, URL inyectada desde `DATABASE_URL`). El seed vive en `backend/src/seed.py`.

El VPS **effi4tech** ya hospeda EffiGuard y expone recursos compartidos: un contenedor `nginx_proxy`, la red Docker externa `general-net` y el cert wildcard `*.effi4tech.cl` (`/etc/letsencrypt/live/effi4tech.cl-0001/`). Traemos una receta CI/CD probada de otro proyecto y la adaptamos a la estructura real de éste.

Decisiones ya tomadas con el usuario: **slug `efficar`**, deploy en **push a `main`**, **seed completo** (`seed.py` tal cual) en el primer arranque, y alcance **backend + backoffice** (la landing Next.js queda fuera).

## Goals / Non-Goals

**Goals:**
- Deploy automático a producción en cada push a `main`: build de imágenes → Docker Hub → deploy SSH al VPS.
- Migraciones (`alembic upgrade head`) y seed automáticos en el arranque del backend.
- Backoffice servido por nginx como SPA, con proxy inverso al backend en el mismo origen (`/api/v1`, `/media`, docs).
- Aislamiento total respecto a EffiGuard salvo los tres recursos compartidos (nginx_proxy, `general-net`, cert wildcard).
- Alta de tenants por subdominio `efficar-<slug>.effi4tech.cl` con un script reproducible.

**Non-Goals:**
- Landing pública Next.js (aún no existe).
- Entorno de staging separado (solo dev local + prod por ahora).
- Estrategia de blue/green o zero-downtime avanzada (deploy es `pull && up -d`, breve corte aceptable).
- Backups automáticos de la BD (se documentan como pendiente operativo, fuera de este change).

## Decisions

### 1. Dockerfiles de prod separados de los de dev
`Dockerfile` actual queda para dev (hot-reload, código como volumen). Se agregan `*.Dockerfile.prod` que copian el código a la imagen (sin volumen) para inmutabilidad. **Alternativa descartada:** un solo Dockerfile multi-stage con target dev/prod — más frágil de mantener y el dev ya funciona.

### 2. Entrypoint del backend: espera DB → migra → seed → uvicorn
`backend/entrypoint.sh` (adaptado: servicio `db`, usuario `efficar`, módulo `src.main:app`):

```sh
#!/bin/sh
set -e
echo "Esperando que PostgreSQL este listo..."
until pg_isready -h "${POSTGRES_HOST:-db}" -U "${POSTGRES_USER:-efficar}"; do sleep 1; done
echo "PostgreSQL listo. Ejecutando migraciones..."
alembic upgrade head
echo "Sembrando datos base (idempotente)..."
python -m src.seed || echo "Seed omitido/ya aplicado"
echo "Iniciando aplicacion..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
```

- **Cambios vs receta original:** `-h db` (no `postgres`), `-U efficar`, `src.main:app` (no `app.main:app`), y se agrega el paso de seed.
- **El seed ya crea el primer tenant y su acceso:** `seed.py` hoy siembra el tenant `vendemostuautomovil.com` (con sus datos corporativos y sucursales), el `SuperAdmin` (Marcelo Moya, `mmoyainfo@gmail.com`), el equipo real de `TENANT_USERS` y un tenant demo. Por lo tanto, tras el primer deploy el login funciona sin ningún alta manual en la BD: el subdominio solo enruta, y la fila del tenant + su admin ya existen. Ya usa el helper `_get_or_create`, base de la idempotencia.
- **Requisito de idempotencia (endurecer):** como el seed corre en **cada** arranque, TODA inserción debe pasar por `_get_or_create` (o upsert por clave natural). Auditar que no queden `db.add(...)` sin guardia que dupliquen al reiniciar. **Alternativa descartada:** seed manual por SSH — se pidió seed completo automático; la idempotencia lo hace seguro ante reinicios.

### 3. nginx del backoffice: proxy `/media`, no `/static`
`backoffice/nginx.prod.conf` sirve la SPA (`try_files $uri $uri/ /index.html`) y proxea al backend:
- `location /api/v1` → `http://backend:8000`
- `location ~ ^/(docs|redoc|openapi.json)` → `http://backend:8000`
- `location /media` → `http://backend:8000` **(adaptación: este proyecto sirve archivos subidos en `/media` vía `StaticFiles`, no en `/static`)**
- Assets estáticos (`js|css|png|jpg|webp|svg|woff2|...`) con `expires 1y; add_header Cache-Control immutable`.

### 4. Frontend se buildea con `VITE_API_URL=/api/v1` (relativo)
El backoffice hoy usa `VITE_API_URL=http://localhost:8000/api/v1` (absoluto). En prod se buildea con valor **relativo** para que las llamadas salgan al mismo origen del SPA y nginx las proxee al backend. El valor se pasa como `--build-arg`/env en el build de la imagen (y como secret `VITE_API_URL` si se prefiere parametrizar). **Alternativa descartada:** URL absoluta por tenant — obligaría a rebuild por subdominio; el proxy same-origin lo evita.

### 5. Un solo backend/backoffice multitenant, subdominios como enrutamiento/branding
La multitenancy es por fila (`tenant_id` en el JWT). Todos los subdominios `efficar-<slug>.effi4tech.cl` apuntan al **mismo** contenedor `efficar_frontend` (igual que la receta original). El tenant se resuelve por el usuario autenticado, no por dominio, en el backoffice. `add-tenant.sh` solo crea el vhost nginx. Para el **primer** tenant (`vendemostuautomovil`) el alta en la BD ya la hace el seed (ver decisión 2), así que no hay paso manual. Para tenants **futuros** distintos del sembrado, el alta de la fila en `tenants` + su admin es un paso aparte (por UI de SuperAdmin o extendiendo el seed).

### 6. docker-compose.prod.yml aislado, unido a red externa
Servicios `db` (postgres:15, volumen `efficar_pgdata`), `backend` (imagen Docker Hub `<user>/efficar-backend`), `backoffice` (imagen `<user>/efficar-frontend`). `container_name` con prefijo `efficar_`. Se unen a la red externa `general-net` (declarada `external: true`, NO se recrea) para que `nginx_proxy` alcance a `efficar_frontend`. La BD y el backend quedan en red interna; solo el frontend necesita ser visible al proxy.

### 7. Deploy por SSH con `docker compose pull && up -d`
El job de Actions: (a) login Docker Hub, build+push de ambas imágenes tageadas por SHA y `latest`; (b) `ssh` al VPS → `cd /root/docker/efficar && docker compose pull && docker compose up -d`. **Alternativa descartada:** `docker context`/registry webhook — SSH directo es lo que ya usa la receta y el VPS.

## Risks / Trade-offs

- **Seed no idempotente corrompe/duplica datos en cada reinicio** → Auditar `seed.py` y garantizar upserts por clave natural antes de habilitar el seed en el entrypoint; si no se puede a tiempo, gatear con una marca (`SEED_ON_START=false`) y sembrar una vez manualmente.
- **Trabajo actual en `master`, deploy en `main`** → Documentar el merge/PR `master → main`; nada se despliega hasta integrar. Riesgo de "empujé a master y no pasó nada".
- **`general-net` o `nginx_proxy` no existen / nombres distintos en el VPS** → Verificar en el VPS antes del primer deploy (`docker network ls | grep general-net`); documentar en pasos manuales. No recrear.
- **Colisión de puertos/nombres con EffiGuard** → Prefijo `efficar_` en contenedores, imágenes propias, volumen `efficar_pgdata`; el backend/DB no publican puertos al host en prod (solo red interna), evitando choque con el 5432/8000 de otros stacks.
- **`VITE_API_URL` mal seteado en build** → Si queda absoluto apuntando a localhost, el SPA en prod falla; se fija relativo en el build de la imagen y se valida en el primer deploy.
- **Migración destructiva o fallida bloquea el arranque** → `alembic upgrade head` corre antes de uvicorn; si falla, el contenedor no levanta (fail-fast, correcto). Mitigación: revisar migraciones en PR y tener el volumen de BD respaldado antes de deploys con DDL fuerte.
- **Secrets faltantes en GitHub** → El workflow falla temprano en login/ssh; documentar la lista completa de secrets como prerequisito.

## Migration Plan

1. Crear los archivos del change (Dockerfiles.prod, entrypoint, nginx conf, compose.prod, workflow, plantilla tenant, script).
2. Asegurar idempotencia del seed (o gatearlo).
3. Configurar secrets en GitHub.
4. Preparar el VPS: `mkdir -p /root/docker/efficar`, crear `.env` de prod, verificar `general-net` y `nginx_proxy`.
5. Integrar a `main` → primer deploy automático.
6. `./scripts/add-tenant.sh vendemostuautomovil` + crear el tenant en la BD.
7. **Rollback:** re-desplegar el tag anterior (imágenes quedan en Docker Hub por SHA); para datos, restaurar volumen `efficar_pgdata` desde backup si una migración fue destructiva.

## Open Questions

- ¿`seed.py` ya es idempotente? (determina si el seed va en el entrypoint o se gatea). Se resuelve al auditarlo en implementación.
- ¿Backups de la BD de prod — se atacan en un change aparte? (fuera de alcance aquí, pero necesario antes de datos reales).
