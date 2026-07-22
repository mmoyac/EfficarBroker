## ADDED Requirements

### Requirement: Disparador de deploy por rama main
El pipeline SHALL ejecutarse automáticamente en cada `push` a la rama `main` y SHALL NOT desplegar desde otras ramas (`master`, feature branches).

#### Scenario: Push a main dispara el deploy
- **WHEN** se integra código a `main` (merge de PR o push directo)
- **THEN** GitHub Actions ejecuta el workflow de build y deploy a producción

#### Scenario: Push a otra rama no despliega
- **WHEN** se hace push a `master` o a una feature branch
- **THEN** el workflow de deploy NO se ejecuta y producción queda intacta

### Requirement: Repositorio y secrets en GitHub como prerrequisito
El pipeline SHALL requerir que el repositorio esté alojado en GitHub con el workflow commiteado y los secrets configurados en Settings → Secrets → Actions.

#### Scenario: Secrets requeridos presentes
- **WHEN** están configurados `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `VPS_HOST`, `VPS_USERNAME`, `VPS_SSH_KEY`, `VPS_PORT` (opcional, default 22), `JWT_SECRET` y las `VITE_*` necesarias para el build
- **THEN** el workflow puede autenticarse en Docker Hub y en el VPS y completar el deploy

#### Scenario: Falta un secret crítico
- **WHEN** falta `DOCKER_PASSWORD` o `VPS_SSH_KEY`
- **THEN** el workflow falla en el paso de login/ssh sin publicar imágenes ni tocar el VPS

### Requirement: Build y publicación de imágenes Docker
El pipeline SHALL construir dos imágenes de producción (`efficar-backend` y `efficar-frontend`) desde sus respectivos `Dockerfile.prod` y publicarlas en Docker Hub tageadas por SHA de commit y por `latest`.

#### Scenario: Build exitoso de ambas imágenes
- **WHEN** el workflow corre tras un push a `main`
- **THEN** se construyen y publican `<DOCKER_USERNAME>/efficar-backend:<sha>` y `:latest`, y `<DOCKER_USERNAME>/efficar-frontend:<sha>` y `:latest`

#### Scenario: El frontend se construye con API base relativa
- **WHEN** se construye la imagen `efficar-frontend`
- **THEN** el build de Vite usa `VITE_API_URL=/api/v1` para que el SPA llame al backend por el mismo origen vía nginx

### Requirement: Deploy remoto por SSH
El pipeline SHALL desplegar conectándose por SSH al VPS y ejecutando `docker compose pull` y `docker compose up -d` en el directorio del proyecto.

#### Scenario: Deploy aplica la nueva imagen
- **WHEN** las imágenes ya están publicadas en Docker Hub
- **THEN** el workflow ejecuta por SSH `cd /root/docker/efficar && docker compose pull && docker compose up -d`, dejando corriendo la versión nueva

### Requirement: Migraciones y seed automáticos en el arranque de producción
El backend en producción SHALL esperar a que Postgres esté disponible, aplicar `alembic upgrade head` y sembrar los datos base antes de aceptar tráfico. El seed SHALL crear el primer tenant y su acceso, y SHALL ser idempotente para poder ejecutarse en cada arranque sin duplicar datos.

#### Scenario: Arranque con base vacía
- **WHEN** el contenedor backend arranca contra una base recién creada
- **THEN** espera a la DB, aplica todas las migraciones, siembra catálogos/roles/menús, el tenant `vendemostuautomovil` con su SuperAdmin y equipo, y recién entonces inicia uvicorn

#### Scenario: Login disponible sin alta manual en la BD
- **WHEN** finaliza el primer deploy y el seed corrió
- **THEN** existe el tenant `vendemostuautomovil` y su usuario admin, y es posible iniciar sesión sin ejecutar ningún INSERT manual en la base

#### Scenario: Reinicio con base ya poblada
- **WHEN** el contenedor backend se reinicia sobre una base ya migrada y sembrada
- **THEN** `alembic upgrade head` no aplica nada nuevo y el seed no duplica filas (upsert por clave natural)

#### Scenario: Migración falla
- **WHEN** `alembic upgrade head` retorna error
- **THEN** el contenedor no inicia uvicorn (fail-fast) y el deploy queda evidenciado como fallido
