## Context

El backoffice es una SPA de Vite + React 18 + Tailwind servida por nginx ([backoffice/nginx.prod.conf](backoffice/nginx.prod.conf)). Un **mismo build** se sirve a todos los tenants; cada automotora entra por su propio dominio y el `tenant_id` se resuelve por dominio/JWT (ver `arquitectura-back-unico-multitenant`). Hoy no hay nada de PWA: [index.html](backoffice/index.html) no tiene `manifest`, no hay service worker, no hay carpeta `public/` ni iconos.

El modelo `Tenant` ([backend/src/models/tenant.py](backend/src/models/tenant.py)) ya tiene `nombre`, `dominio` y `logo` (URL o data-URI). **No** guarda colores de marca: la paleta (`#FFD701` / `#222732`) está hardcodeada en `tailwind.config.js` y es común a todos los tenants por ahora.

**Auditoría del estado responsive actual (lo que ya hay codeado):**
- **Navegación no responsive (bloqueante):** [Layout.tsx](backoffice/src/components/Layout.tsx) monta un `<div class="flex">` con [Sidebar.tsx](backoffice/src/components/Sidebar.tsx) como `<aside class="h-screen w-64">` **siempre visible, sin ningún breakpoint**, y el `<main>` usa `p-8`. En un móvil de 320 px el sidebar fijo de 256 px deja ~64 px de contenido → inservible. Es el punto #1 a resolver.
- **9 páginas con `<table>` crudas** que desbordan en horizontal en móvil: Vehículos, Actas, Comisiones, DerivadasVentas, MisCaptaciones, OrdenesPago, Tasación, Users y ActaDetalle. Ninguna tiene hoy tratamiento móvil.
- **Ya responsive (no requieren rehacerse):** los `grid` de tarjetas/formularios usan prefijos `sm:`/`lg:` y colapsan a 1 columna en móvil (Dashboard, Tasación, EstadoResultado, Comisiones, NuevaActa, CatalogoVehicular). Los grids internos de los modales `RecepcionarModal`/`EditarActaModal` apilan en móvil (`grid-cols-1` → `sm:grid-cols-12`). El trabajo responsive real se concentra en **nav + tablas + paddings/viewport**, no en todo el front.
- **Falta viewport-fit/safe-area:** [index.html](backoffice/index.html) declara `viewport` básico sin `viewport-fit=cover`; `index.css`/`tailwind.config.js` no tienen utilidades de safe-area.

El patrón dominio→tenant fue **especificado** en la change `galeria-multimedia-vehiculo` (capacidad `catalogo-publico`), pero su backend quedó **diferido y NO codeado**: no existe `src/routers/public.py` ni ninguna dependency que resuelva el tenant por `Host`. Hoy toda la resolución de tenant es por **JWT** ([dependencies.py](backend/src/dependencies.py): `get_current_tenant` → `get_effective_tenant_id`). Por tanto **esta change construye** la resolución host→tenant desde cero y la deja como mecanismo compartido que el catálogo público podrá reutilizar.

**Topología de producción (verificada en las configs del deploy) — corrige un supuesto inicial:** el backoffice NO se sirve en `Tenant.dominio` (la landing `.com`). Se sirve por tenant en el subdominio `efficar-<slug>.effi4tech.cl` (todos los tenants sobre el MISMO contenedor `efficar_frontend`; ver [nginx-efficar.conf](nginx-efficar.conf) y [DEPLOY.md](DEPLOY.md)), la API vive aparte en `efficar-api.effi4tech.cl`, y la multitenancy de la app es **por JWT**, no por dominio. Consecuencia: resolver por `Tenant.dominio == host` daría siempre la identidad por defecto en prod. **Solución adoptada:** se añade `Tenant.slug` (el `<slug>` del subdominio del backoffice), y `get_tenant_by_host` extrae el slug de `<APP_HOST_PREFIX><slug><APP_HOST_SUFFIX>` y lo busca en `Tenant.slug`, con fallback al match por `Tenant.dominio` para la landing futura. El slug lo siembra el seed (backfill del tenant real), así que un deploy lo aplica sin pasos manuales en el VPS.

Restricciones duras del proyecto: multitenancy no negociable; todo enum es catálogo; API versionada `/api/v1/`; TS strict; ejecución en Docker.

Decisiones ya tomadas con el usuario:
- Iconos: derivar del `logo` del tenant por defecto, dejando override futuro.
- Manifest: endpoint **dinámico host-aware en el backend**.
- Alcance PWA: **instalable + app shell** (sin offline de datos).
- UI móvil: **auditoría responsive incremental** (adaptar pantallas, no rediseñar).

## Goals / Non-Goals

**Goals:**
- Que el backoffice sea instalable ("Agregar a pantalla de inicio") en Android (Chrome) e iOS (Safari), con app shell cacheado para arranque rápido.
- Que la app instalada muestre el **nombre e icono del tenant** correspondiente al dominio por el que se instaló.
- Servir `manifest` e iconos desde el backend resolviendo el tenant por `Host`, con un solo build de front y cero provisión por dominio.
- Derivar los iconos del `logo` del tenant, con un contrato que admita a futuro un set dedicado, sin tocar el front.
- Operabilidad plena en móviles de 5" (~320–360 px) adaptando las pantallas actuales.
- Ciclo de actualización que no deje al usuario con un shell obsoleto tras deploy.

**Non-Goals:**
- Offline de datos, cola de sincronización o mutaciones sin señal (diferido).
- UI de backoffice para que el tenant suba su propio set de iconos (solo se deja el contrato).
- Rediseño mobile-first de flujos o cambio de arquitectura de navegación.
- Colores/tema por tenant en la UI (la paleta sigue común; solo `theme-color`/fondo del manifest se derivan por tenant).
- Push notifications (fuera de alcance).

## Decisions

### 1. `manifest.webmanifest` dinámico servido por el backend, resuelto por `Host`
Se añade un router público **sin auth** que expone `GET /manifest.webmanifest`. Resuelve el tenant con una **nueva dependency de host** (lookup `Tenant.dominio == Host`, que el catálogo público futuro reutilizará) y devuelve un manifest con `name`/`short_name` = `tenant.nombre`, `start_url`/`scope` = `/`, `display: standalone`, `theme_color`/`background_color` por defecto de marca, y las entradas `icons` apuntando a las rutas de icono del backend. Si el host no está mapeado, devuelve la **identidad por defecto** de EffiCarBroker (no `404`: la app genérica debe seguir siendo instalable en dev/staging).

- **Por qué:** un solo build de Vite sirve a N dominios; un manifest estático no puede variar `name`/icono por tenant. El backend ya sabe resolver dominio→tenant.
- **Alternativa descartada — manifest estático por dominio en nginx:** obligaría a provisionar archivos por cada alta de tenant y a plantillas de nginx por dominio; se descartó por operación.
- **Alternativa descartada — generar el manifest en runtime en el cliente (Blob URL):** frágil en iOS, peor cacheabilidad y no resuelve `apple-touch-icon` (que Safari lee del HTML). Se descarta.

### 2. Iconos derivados del `logo` del tenant, con contrato para override
`GET /app-icons/icon-{size}.png` (tamaños 192, 512), `GET /app-icons/maskable-{size}.png` y `GET /app-icons/apple-touch-icon.png`. El backend toma el `logo` del tenant (URL o data-URI), lo normaliza a PNG cuadrado con fondo seguro y padding para `maskable` (zona segura ~80%), redimensiona al tamaño pedido y cachea el resultado (por `tenant_id` + tamaño + hash del logo). Si el tenant no tiene `logo`, usa el icono por defecto de EffiCarBroker.

- **Override futuro:** el contrato de ruta no cambia; cuando exista un set dedicado (nuevas columnas/tabla de assets del tenant), el servicio prioriza ese asset sobre el logo. Esta change no crea esa UI ni esas columnas — solo deja el punto de extensión documentado.
- **Por qué derivar del logo:** los tenants ya cargan su logo para el acta/PDF; reutilizarlo evita otro paso de alta. Riesgo: un logo rectangular o con fondo transparente puede verse mal recortado — se mitiga con fondo/padding y se documenta la recomendación de subir un logo cuadrado.
- **Dependencia:** Pillow en el backend para el redimensionado.

### 3. iOS necesita el `apple-touch-icon` y metas en el HTML, no solo el manifest
Safari/iOS ignora en buena parte el manifest para el icono de home screen y usa `<link rel="apple-touch-icon">` y metas `apple-mobile-web-app-*` del `index.html`. Como el HTML es el mismo build para todos los tenants, el `<link rel="apple-touch-icon" href="/app-icons/apple-touch-icon.png">` apunta a la **ruta host-aware** del backend: el propio Safari pide esa URL a su dominio y el backend responde el icono del tenant. Igual para `<link rel="manifest" href="/manifest.webmanifest">`.

- **Por qué:** es la única forma de tener icono correcto por tenant en iOS con un solo `index.html`. La resolución vuelve a ocurrir en el servidor por `Host`.

### 4. Service worker de app shell con Vite (network-first para navegación)
Se usa `vite-plugin-pwa` (Workbox) en modo `injectManifest` o `generateSW` con: **precache** de los assets con hash del build (JS/CSS/fuentes), **network-first** para las navegaciones (para no servir un `index.html` viejo), y **NetworkOnly** para todo lo bajo `/api/` y `/media/` (nunca cachear datos ni respuestas autenticadas — coherente con "sin offline de datos"). El SW se registra en [main.tsx](backoffice/src/main.tsx).

- **`manifest.webmanifest` e iconos NO se precachean** (son host-aware del backend): se dejan pasar a la red.
- **Alternativa descartada — SW artesanal:** más código y trampas de caché; Workbox cubre precache+update de forma probada.

### 5. Actualización: avisar y refrescar, sin auto-recargar destructivo
Con `registerType: 'prompt'`: cuando hay un nuevo SW en espera, se muestra un aviso discreto ("Nueva versión disponible — Actualizar") que hace `skipWaiting` + reload. Evita recargar en medio de un formulario del ejecutivo.

- **Por qué prompt y no autoUpdate:** un ejecutivo a mitad de una recepción/venta no debe perder el formulario por una recarga silenciosa.

### 6. nginx debe enrutar manifest e iconos al backend
La config actual ([backoffice/nginx.prod.conf](backoffice/nginx.prod.conf)) tiene una regla de assets estáticos con `expires 1y; immutable` que atraparía `manifest.webmanifest`/`*.png`, y un fallback SPA que devuelve `index.html`. Se agregan `location = /manifest.webmanifest` y `location /app-icons/` que hacen `proxy_pass` al backend (como ya se hace con `/api/v1` y `/media`), **antes** de las reglas genéricas, con cache corta/revalidable (el icono depende del tenant y puede cambiar).

### 7. Responsive incremental: breakpoint móvil, nav adaptativa y tabla→tarjetas
- **Navegación:** el `Sidebar` fijo pasa a **drawer** (off-canvas con overlay) bajo `md`, con un botón hamburguesa en el header; se evalúa bottom-nav para las 3–4 acciones más usadas por el ejecutivo. `TenantSwitcher` y menú por rol se mantienen dentro del drawer.
- **Listados:** las tablas anchas (Vehículos, Actas, Comisiones, Órdenes de pago, Usuarios) adoptan un patrón **tabla en ≥md / tarjetas apiladas en <md**, mostrando por tarjeta los 3–4 campos clave + acciones.
- **Formularios y modales:** modales a ancho completo con scroll interno en móvil; inputs y botones con objetivo táctil ≥44 px; se verifican a 320–360 px.
- **Viewport/safe-area:** `viewport-fit=cover` + utilidades `env(safe-area-inset-*)` para notch/barra iOS; `theme-color` coherente.
- **Enfoque:** se hace pantalla por pantalla reutilizando Tailwind; no se introduce una librería de UI nueva ni se reescriben flujos.

## Risks / Trade-offs

- **Logo no cuadrado / con transparencia se ve mal como icono** → normalizar a cuadrado con fondo y padding `maskable`; documentar recomendación de logo cuadrado; dejar override dedicado como salida.
- **`tenant.logo` es `String(500)`** (verificado en implementación): un data-URI de una imagen raster real NO cabe en 500 chars → en la práctica el logo usado para iconos debe ser una **URL http** (coherente con las URLs de cloud que ya usa la galería), no un data-URI. El servicio de iconos soporta ambos, pero si se quiere admitir data-URIs grandes habría que ampliar la columna (migración) o mover el asset a storage. Mitigación actual: si no hay logo utilizable, el icono cae a las **iniciales del tenant sobre la marca** (probado y on-brand).
- **iOS es limitado con PWA** (sin prompt de instalación, soporte parcial de SW, caché de `apple-touch-icon` agresiva) → apoyarse en metas del HTML apuntando a rutas host-aware; documentar el flujo manual "Compartir → Agregar a inicio"; versionar la URL del icono para forzar refresh cuando cambie el logo.
- **Cachear el shell puede servir una versión vieja tras deploy** → navegación network-first + update `prompt`; nunca precachear `index.html` como cache-first.
- **Confundir "instalable" con "offline"** → el SW es NetworkOnly para `/api` y `/media`; sin señal la app abre pero las vistas con datos fallan como hoy. Explícito como Non-Goal.
- **nginx atrapa manifest/iconos con la regla `immutable`** → rutas dedicadas con `proxy_pass` y cache corta antes de las reglas genéricas; verificar orden de `location`.
- **Costo de redimensionar iconos en cada request** → cache por tenant+size+hash del logo; invalidar al cambiar el logo.

## Migration Plan

1. Backend: dependency de host (reutilizada), servicio de iconos (Pillow) + router público de manifest/iconos; identidad y colores por defecto en `settings.py`. Sin migración de BD (usa `logo` existente).
2. Front: `vite-plugin-pwa`, metas en `index.html`, registro de SW + aviso de actualización.
3. nginx: rutas de manifest/iconos al backend (afecta prod; en dev el `proxy` de Vite o acceso directo al backend).
4. Responsive: iterar pantalla por pantalla detrás del trabajo PWA; se puede desplegar por partes.
5. Verificación: Lighthouse PWA (installable), prueba real de instalación en Android e iOS con dos dominios distintos mostrando icono/nombre distinto; revisión a 320–360 px.
6. **Rollback:** quitar los `<link>` del HTML y no registrar el SW deja el backoffice como estaba; para purgar un SW ya instalado se publica un SW "kill-switch" que se desregistra (mitiga clientes con SW viejo cacheado).

## Open Questions

- ¿Bottom-nav además del drawer, o solo drawer? (se decide al auditar las pantallas más usadas por el ejecutivo).
- ¿`theme_color`/`background_color` del manifest fijos de marca EffiCarBroker, o también derivados por tenant a futuro cuando existan colores por tenant? (por ahora fijos).
- Nombre exacto de rutas de icono (`/app-icons/...` vs `/pwa/...`) — cosmético; se fija en tasks.
