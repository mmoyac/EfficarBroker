# Deploy — CI/CD al VPS effi4tech

Pipeline: **push a `main`** → GitHub Actions construye las imágenes (`efficar-backend`,
`efficar-frontend`), las publica en Docker Hub y despliega por SSH al VPS
(`docker compose pull && up -d`). El backend, al arrancar, espera a Postgres, corre
`alembic upgrade head` y siembra los datos base (idempotente).

> El deploy solo se dispara desde `main`. El trabajo en `master`/features no despliega
> nada hasta integrarse a `main`.

---

## 1. Secrets de GitHub (Settings → Secrets and variables → Actions)

| Secret | Descripción |
|---|---|
| `DOCKER_USERNAME` | Usuario de Docker Hub |
| `DOCKER_PASSWORD` | Token/clave de Docker Hub |
| `VPS_HOST` | IP o host del VPS |
| `VPS_USERNAME` | Usuario SSH (ej. `root`) |
| `VPS_SSH_KEY` | Clave privada SSH (contenido completo) |
| `VPS_PORT` | Puerto SSH (opcional, default 22) |

> `JWT_SECRET` y `SEED_DEFAULT_PASSWORD` NO son secrets de Actions: viven en el `.env`
> del VPS. `VITE_API_URL` se fija en el build como `/api/v1` (no requiere secret).

---

## 2. Preparación del VPS (una sola vez, a mano)

El pipeline **no crea** la carpeta ni el `.env`: deben existir antes del primer deploy.

```sh
# 2.1 Carpeta del proyecto (aislada de EffiGuard)
mkdir -p /root/docker/efficar && cd /root/docker/efficar

# 2.2 Verificar que la red compartida existe (por EffiGuard). NO recrear.
docker network ls | grep general-net

# 2.3 Verificar que el nginx_proxy y el cert wildcard *.effi4tech.cl existen
# (los certs viven en el volumen del contenedor, no en el host)
docker ps | grep nginx_proxy
docker exec nginx_proxy ls /etc/letsencrypt/live/effi4tech.cl-0001/
```

Copiar al VPS, dentro de `/root/docker/efficar/`:
- `docker-compose.prod.yml`
- `nginx-efficar.conf`
- `scripts/add-tenant.sh`  (junto a `nginx-efficar.conf`)

Crear el `.env` a partir de [.env.prod.example](.env.prod.example) y completar los
valores `CAMBIAR_*` (incluye `DOCKER_USERNAME`, credenciales de Postgres, `DATABASE_URL`,
`JWT_SECRET`, `BACKEND_CORS_ORIGINS`, `SEED_DEFAULT_PASSWORD`).

---

## 3. Primer deploy

1. Enlazar el remoto (ya hecho): `git remote add origin https://github.com/mmoyac/EfficarBroker.git`
2. Integrar el trabajo a `main` (merge de `master` o promover `master` a default en GitHub).
3. `git push origin main` → GitHub Actions construye y despliega.
4. Verificar en el VPS: `docker ps` debe mostrar `efficar_db`, `efficar_backend`, `efficar_frontend` en `Up`.
5. Logs del backend (migraciones + seed): `docker logs -f efficar_backend`.

---

## 4. Alta de tenant (subdominio)

```sh
cd /root/docker/efficar
./add-tenant.sh vendemostuautomovil
# -> genera /root/docker/nginx-proxy/conf.d/efficar-vendemostuautomovil.conf
#    y recarga nginx. Queda en https://efficar-vendemostuautomovil.effi4tech.cl
```

- El tenant `vendemostuautomovil` **ya existe en la BD** (lo crea el seed), así que el
  login funciona sin pasos extra.
- Para un tenant **nuevo distinto**, además del vhost hay que crear su fila en `tenants`
  y sus usuarios (por UI de SuperAdmin o extendiendo el seed).

---

## 5. Aislamiento respecto a EffiGuard (IMPORTANTE)

Carpeta propia (`/root/docker/efficar`), imágenes Docker Hub propias (`efficar-*`),
contenedores con prefijo `efficar_` y volúmenes propios (`efficar_pgdata`, `efficar_media`).
Se comparten SOLO: el `nginx_proxy`, la red `general-net` y el cert `*.effi4tech.cl`.
**No tocar nada de `/root/docker/EffiGuard/`.**

---

## 6. Rollback

Las imágenes quedan tageadas por SHA en Docker Hub. Para volver a una versión anterior:

```sh
cd /root/docker/efficar
# editar docker-compose.prod.yml para fijar el tag :<sha> anterior, o:
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Para datos, restaurar el volumen `efficar_pgdata` desde backup si una migración fue
destructiva. **Pendiente operativo (fuera de este change): backups automáticos de la BD.**
