## Why

Hoy EffiCarBroker solo corre en local (`docker-compose` con hot-reload) y no existe forma de desplegarlo a producción. Necesitamos un pipeline CI/CD reproducible que publique la app en el VPS **effi4tech** (el mismo que ya hospeda EffiGuard) cada vez que se integra a `main`, reutilizando una receta ya probada en otro proyecto y adaptándola a la estructura real de este monorepo (`backend/src`, `backoffice/`, servicio DB `db`, media en `/media`).

## What Changes

- **Nuevos artefactos de build de producción** (separados de los de dev, que se conservan):
  - `backend/Dockerfile.prod` + `backend/entrypoint.sh`: espera a Postgres, corre `alembic upgrade head`, siembra (seed) en el primer arranque y lanza `uvicorn src.main:app` con workers.
  - `backoffice/Dockerfile.prod` + `backoffice/nginx.prod.conf`: build de Vite servido por nginx como SPA, con proxy inverso a `backend:8000` para `/api/v1`, `/media` y `/(docs|redoc|openapi.json)`.
- **`docker-compose.prod.yml`**: stack de producción (db + backend + backoffice) con prefijo `efficar_`, volumen de BD propio, unido a la red externa `general-net`. Aislado de EffiGuard.
- **Workflow de GitHub Actions** (`.github/workflows/deploy.yml`): en push a `main` construye y publica las imágenes en Docker Hub y despliega vía SSH al VPS (`docker compose pull && up -d`).
- **Plantilla de tenant** `nginx-efficar.conf` + `scripts/add-tenant.sh`: alta de subdominios `efficar-<slug>.effi4tech.cl` sobre el `nginx_proxy` compartido, con el cert wildcard `*.effi4tech.cl`.
- **Config de build del frontend para prod**: `VITE_API_URL` relativo (`/api/v1`) para que el SPA llame al backend por el mismo origen a través de nginx.
- **Documentación de secrets de GitHub y pasos manuales del VPS** en el README/design.
- **BREAKING (flujo de trabajo, no de runtime):** el deploy se dispara desde `main`; el trabajo actual en `master` deberá integrarse a `main` (merge o PR) para desplegarse.

## Capabilities

### New Capabilities
- `ci-cd-pipeline`: Integración y despliegue continuo — disparador por rama, build y publicación de imágenes Docker, deploy remoto por SSH, secrets requeridos, y ejecución automática de migraciones + seed en el arranque de producción.
- `deployment-topology`: Topología de despliegue en el VPS effi4tech — contenedores/imágenes/volúmenes propios con prefijo `efficar`, aislamiento respecto a EffiGuard, recursos compartidos (nginx_proxy, red `general-net`, cert wildcard), enrutamiento por subdominio de tenant y proxy inverso nginx (SPA + `/api/v1` + `/media` + docs).

### Modified Capabilities
<!-- Ninguna: no cambian requisitos de capacidades de negocio existentes; esto es infraestructura nueva. -->

## Impact

- **Nuevos archivos:** `backend/Dockerfile.prod`, `backend/entrypoint.sh`, `backoffice/Dockerfile.prod`, `backoffice/nginx.prod.conf`, `docker-compose.prod.yml`, `.github/workflows/deploy.yml`, `nginx-efficar.conf`, `scripts/add-tenant.sh`.
- **Sin cambios en código de aplicación** (routers, modelos, schemas): la app ya expone `src.main:app`, sirve `/media` vía `StaticFiles` y migra con Alembic (`backend/migrations`). El seed reutiliza `backend/src/seed.py` tal cual.
- **Frontend:** el build de producción se parametriza con `VITE_API_URL=/api/v1`; el dev sigue usando la URL absoluta actual.
- **Infra del VPS (manual, documentado):** carpeta `/root/docker/efficar`, `.env` de producción, alta de tenants por subdominio. Depende de recursos ya existentes en el VPS: `nginx_proxy`, red `general-net`, cert `*.effi4tech.cl`.
- **GitHub:** requiere configurar secrets (`DOCKER_USERNAME/PASSWORD`, `VPS_HOST/USERNAME/SSH_KEY/PORT`, `JWT_SECRET`, `VITE_*`).
- **Riesgo controlado:** no se toca nada de `/root/docker/EffiGuard/`; imágenes, contenedores y volumen de BD son independientes.
