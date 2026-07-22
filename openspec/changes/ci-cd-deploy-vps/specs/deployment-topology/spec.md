## ADDED Requirements

### Requirement: Aislamiento respecto a EffiGuard en el VPS
El stack de producción SHALL correr aislado de EffiGuard: carpeta propia, imágenes Docker Hub propias, contenedores con prefijo `efficar_` y volumen de BD propio. SHALL compartir únicamente el contenedor `nginx_proxy`, la red externa `general-net` y el cert wildcard `*.effi4tech.cl`. NO SHALL modificar nada bajo `/root/docker/EffiGuard/`.

#### Scenario: Contenedores y volúmenes propios
- **WHEN** el stack se levanta en el VPS
- **THEN** los contenedores son `efficar_db`, `efficar_backend`, `efficar_frontend` y usan el volumen `efficar_pgdata`, sin colisionar con nombres/volúmenes de EffiGuard

#### Scenario: Red externa no se recrea
- **WHEN** el compose de producción se ejecuta
- **THEN** se une a la red `general-net` declarada como `external: true` y no intenta crearla ni recrearla

### Requirement: Directorio y configuración manual en el VPS
El VPS SHALL tener creados a mano, una sola vez antes del primer deploy, el directorio del proyecto y los archivos de arranque que el pipeline no genera.

#### Scenario: Preparación previa al primer deploy
- **WHEN** se prepara el VPS por primera vez
- **THEN** existen `/root/docker/efficar/`, `/root/docker/efficar/docker-compose.prod.yml` y `/root/docker/efficar/.env` (con `POSTGRES_USER/PASSWORD/DB`, `JWT_SECRET` y demás), creados manualmente

#### Scenario: El deploy no crea la carpeta ni el .env
- **WHEN** el pipeline hace `cd /root/docker/efficar`
- **THEN** asume que la carpeta, el compose y el `.env` ya existen; si faltan, el deploy falla (no los genera automáticamente)

### Requirement: Proxy inverso nginx del backoffice
La imagen `efficar-frontend` SHALL servir el SPA del backoffice y actuar como proxy inverso al backend para las rutas de API, media y documentación, en el mismo origen.

#### Scenario: Ruteo de SPA y API
- **WHEN** un request llega a `efficar_frontend`
- **THEN** las rutas de aplicación resuelven con `try_files $uri $uri/ /index.html`, y `/api/v1`, `/media` y `/(docs|redoc|openapi.json)` se proxean a `http://backend:8000`

#### Scenario: Media servida desde el backend
- **WHEN** el SPA solicita una foto de la galería bajo `/media/...`
- **THEN** nginx la proxea al backend (que la sirve vía `StaticFiles`), sin tratarla como ruta del SPA

#### Scenario: Cache de assets estáticos
- **WHEN** se sirven assets con hash (`js`, `css`, imágenes, fuentes)
- **THEN** nginx responde con `expires 1y` y `Cache-Control: immutable`

### Requirement: Enrutamiento por subdominio de tenant
El sistema SHALL exponer cada tenant bajo `efficar-<slug>.effi4tech.cl` sobre el `nginx_proxy` compartido, todos apuntando al mismo contenedor `efficar_frontend`. La resolución del tenant SHALL hacerse por el usuario autenticado (JWT), no por dominio.

#### Scenario: Alta de un tenant nuevo
- **WHEN** se ejecuta `./scripts/add-tenant.sh <slug>` en el VPS
- **THEN** se genera `/root/docker/nginx-proxy/conf.d/efficar-<slug>.conf` desde la plantilla (con HTTP→HTTPS, `.well-known/acme-challenge`, cert wildcard y `proxy_pass http://efficar_frontend:80`) y se recarga nginx (`nginx -t && nginx -s reload`)

#### Scenario: Validación del script de tenant
- **WHEN** se invoca `add-tenant.sh` sin argumento o con un slug que ya tiene vhost
- **THEN** el script aborta con error sin sobrescribir configuración existente

#### Scenario: Primer tenant ya existe en la BD por el seed
- **WHEN** se crea el vhost `efficar-vendemostuautomovil.effi4tech.cl` tras el primer deploy
- **THEN** la fila del tenant `vendemostuautomovil` y su admin ya existen (creados por el seed), y el subdominio solo aporta el enrutamiento HTTPS

#### Scenario: El vhost no crea tenants futuros en la BD
- **WHEN** se crea el vhost de un tenant nuevo distinto del sembrado
- **THEN** el alta de su fila en `tenants` y sus usuarios es un paso separado en la base de datos (UI de SuperAdmin o extensión del seed), no realizado por `add-tenant.sh`
