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

## 4. Alta de un NUEVO tenant (automotora) — runbook

Cada automotora vive en su propio subdominio `efficar-<slug>.effi4tech.cl`, todos
apuntando al MISMO contenedor `efficar_frontend`. La multitenancy es por fila
(`tenant_id` en el JWT): el tenant se resuelve por el usuario que inicia sesión, no
por el dominio. Un tenant nuevo son **3 pasos**:

### Paso 1 — Fila del tenant + su usuario admin en la BD
Un tenant nuevo NO viene sembrado (el seed solo crea `vendemostuautomovil`). Se crea
desde el backoffice con un usuario **SuperAdmin**:

1. Entra como SuperAdmin (`mmoyainfo@gmail.com`).
2. **Panel de Inquilinos → Directorio de Clientes** (`/saas/tenants`): crea el tenant
   (nombre, dominio, datos corporativos) y su primer usuario `TenantAdmin`.

> Alternativa por SQL (avanzado, si no usas la UI): insertar en `tenants` y un `users`
> con `role_id` de `TenantAdmin` y `tenant_id` del nuevo tenant.

### Paso 2 — Vhost nginx en el VPS
```sh
cd /root/docker/efficar
./add-tenant.sh <slug>          # ej: ./add-tenant.sh autoexpress
# genera /root/docker/nginx-proxy/conf.d/efficar-<slug>.conf y recarga nginx.
```
El script valida que el slug no exista y usa el cert wildcard `*.effi4tech.cl` (sin
emitir certificado nuevo).

### Paso 3 — Registro DNS
En el proveedor DNS de `effi4tech.cl` (no hay wildcard DNS; es un registro por
subdominio), agrega:

| Tipo | Nombre | Valor |
|---|---|---|
| A | `efficar-<slug>` | `168.231.96.205` |

Cuando propague, el tenant entra en `https://efficar-<slug>.effi4tech.cl` con el
usuario admin del Paso 1. **No hace falta redeploy ni tocar el cert.**

### Ejemplo real ya montado: `vendemostuautomovil`
- Fila en BD: creada por el seed (con el equipo real).
- Vhost: `./add-tenant.sh vendemostuautomovil` ✅
- DNS: A `efficar-vendemostuautomovil` → `168.231.96.205` ✅
- Vivo en https://efficar-vendemostuautomovil.effi4tech.cl

---

## 4b. Qué siembra el seed (y el flag SEED_DEMO_DATA)

El backend siembra en cada arranque (idempotente, controlado por `SEED_ON_START`):

**Siempre (catálogos + maestras):** roles, ciudades/comunas, estados de vehículo,
marcas/modelos/versiones, checklist del acta, tipos de comisión, menú por rol, el
tenant real `vendemostuautomovil` con sus sucursales y **todo el equipo** (SuperAdmin
`mmoyainfo@gmail.com` + usuarios reales), y sus parámetros de comisión.

**Solo si `SEED_DEMO_DATA=true` (dev):** datos operacionales de prueba (vehículos
`DERV01`/`REING01` con sus actas/captaciones de derivación y reingreso) **y un 2º
tenant demo** (`Automotora Demo`) para probar el cambio de contexto del SuperAdmin.

| Entorno | SEED_ON_START | SEED_DEMO_DATA | Resultado |
|---|---|---|---|
| Producción (`.env` del VPS) | `true` | **`false`** | catálogos + maestras + tenant real + usuarios |
| Desarrollo (`docker-compose.yml`) | (seed manual) | `true` | lo anterior + datos y tenant demo para pruebas |

> Cambiar `SEED_DEMO_DATA` no borra lo ya existente (el seed no hace DELETE). Ponerlo
> en `false` evita crear demo en los PRÓXIMOS arranques/deploys; no limpia lo que ya
> se sembró. Para limpiar demo previo hay que borrarlo a mano en la BD.

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
