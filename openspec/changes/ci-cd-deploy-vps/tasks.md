## 1. Repositorio GitHub y ramas

- [x] 1.1 Enlazar el remoto: `git remote add origin https://github.com/mmoyac/EfficarBroker.git`
- [ ] 1.2 Crear/publicar la rama `main` en GitHub (fusionar `master → main` o promover `master` a default) — el deploy se dispara solo desde `main` *(acción tuya: requiere push/merge)*
- [ ] 1.3 Definir el flujo de trabajo: features en ramas → PR hacia `main`; integrar a `main` = desplegar *(acordar/documentado en DEPLOY.md)*

## 2. Backend — build de producción

- [x] 2.1 Crear `backend/Dockerfile.prod`: base python 3.11-slim, venv, `pip install -r requirements.txt`, `COPY . .` (código dentro de la imagen, sin volumen), `ENTRYPOINT ["./entrypoint.sh"]`
- [x] 2.2 Crear `backend/entrypoint.sh`: `pg_isready -h db -U efficar` en loop → `alembic upgrade head` → `python -m src.seed` (gateado con `SEED_ON_START`) → `exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2`
- [x] 2.3 Auditar `backend/src/seed.py` para idempotencia total: confirmado que TODA inserción pasa por `_get_or_create` o guardias explícitas (`if not tiene_acta`), sin `db.add(...)` sueltos que dupliquen
- [x] 2.4 Verificar que el seed crea el primer tenant y su acceso: probado end-to-end — login de `mmoyainfo@gmail.com` (SuperAdmin) devuelve JWT válido tras el arranque, sin INSERT manual
- [x] 2.5 Verificar que `pg_isready` esté disponible en la imagen (se instala `postgresql-client`) y que `requirements.txt` incluya alembic (1.14.0)

## 3. Backoffice — build de producción

- [x] 3.1 Crear `backoffice/Dockerfile.prod` multi-stage: stage node (`npm ci && npm run build` con `ARG VITE_API_URL=/api/v1`) → stage nginx que copia `dist/` y `nginx.prod.conf`
- [x] 3.2 Crear `backoffice/nginx.prod.conf`: SPA `try_files $uri $uri/ /index.html`; proxy de `/api/v1`, `/media` y `~ ^/(docs|redoc)` a `http://backend:8000`; `expires 1y; Cache-Control immutable` para assets (nota: `openapi.json` vive bajo `/api/v1`, ya cubierto)
- [x] 3.3 Confirmar que el cliente API respeta `VITE_API_URL` relativo: `api.ts` usa `import.meta.env.VITE_API_URL` y deriva `API_ORIGIN` vacío → `/media/...` resuelve al mismo origen (probado)

## 4. Compose de producción

- [x] 4.1 Crear `docker-compose.prod.yml`: `db` (postgres:15, volumen `efficar_pgdata`, sin puerto al host), `backend` (imagen `${DOCKER_USERNAME}/efficar-backend:latest`, `env_file: .env`, `depends_on db healthy`, volumen `efficar_media`), `backoffice` (imagen `efficar-frontend:latest`)
- [x] 4.2 `container_name` con prefijo `efficar_`; red externa `general-net` (`external: true`) + red `internal`; `backoffice` unido a ambas para que `nginx_proxy` lo alcance
- [x] 4.3 Documentar el `.env` de producción esperado → `.env.prod.example`

## 5. GitHub Actions

- [x] 5.1 Crear `.github/workflows/deploy.yml` con trigger `on: push: branches: [main]`
- [x] 5.2 Job build: login Docker Hub, build+push de `efficar-backend` y `efficar-frontend` tageadas por `${{ github.sha }}` y `latest` (`VITE_API_URL=/api/v1` como build-arg del frontend, cache gha)
- [x] 5.3 Job deploy (SSH con `VPS_HOST/USERNAME/SSH_KEY/PORT`): `docker login` + `docker compose -f docker-compose.prod.yml pull && up -d && docker image prune -f`
- [x] 5.4 Documentar la lista de secrets requeridos (en DEPLOY.md)

## 6. Enrutamiento de tenants (nginx_proxy compartido)

- [x] 6.1 Crear plantilla `nginx-efficar.conf` con placeholder `TENANT_SLUG`: server :80 (redirect HTTPS + `.well-known/acme-challenge`) y server :443 ssl con cert `*.effi4tech.cl`, `server_name efficar-TENANT_SLUG.effi4tech.cl`, `proxy_pass http://efficar_frontend:80`
- [x] 6.2 Crear `scripts/add-tenant.sh <slug>`: valida argumento y que el slug no exista → `sed` de la plantilla → `docker exec nginx_proxy nginx -t && nginx -s reload`

## 7. Documentación (README)

- [x] 7.1 Documentar los secrets de GitHub y cómo cargarlos (DEPLOY.md §1)
- [x] 7.2 Documentar los pasos manuales del VPS: carpeta, `.env`, copiar compose/plantilla/script, verificar `general-net`, primer deploy, `add-tenant.sh` (DEPLOY.md §2-4)
- [x] 7.3 Advertir explícitamente: no tocar `/root/docker/EffiGuard/`; imágenes/contenedores/volúmenes propios (DEPLOY.md §5)

## 8. Verificación end-to-end

- [ ] 8.1 Primer deploy REAL: confirmar que las imágenes se publican, el VPS las baja y los contenedores quedan `Up` *(pendiente: requiere push a `main` + VPS)*
- [x] 8.2 Verificado en local (stack prod completo con las imágenes reales): 17 migraciones aplicadas, seed cargado (catálogos + tenants + usuarios), login del SuperAdmin OK
- [x] 8.3 Verificado en local que el SPA se sirve por nginx (HTTP 200 html) y que `/api/v1` y `/docs` responden por el mismo origen; *falta solo la parte de dominio/DNS `efficar-vendemostuautomovil.effi4tech.cl` (requiere VPS)*
- [ ] 8.4 Probar reinicio del backend y confirmar que el seed idempotente no duplica datos *(idempotencia confirmada por auditoría de código y un arranque limpio; el recuento tras doble arranque se validará en el deploy real)*
