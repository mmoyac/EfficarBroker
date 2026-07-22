## Why

Los ejecutivos de captación/venta trabajan en terreno desde el móvil, pero hoy el backoffice es una SPA pensada para escritorio: no se puede "instalar" en el teléfono, no tiene icono propio en la pantalla de inicio y varias pantallas (sidebar fijo, tablas anchas) quedan incómodas en equipos de 5". Además, como el SaaS es multitenant y cada automotora entra por su propio dominio, la app instalada debería mostrar **el icono y el nombre de esa automotora** —no un genérico "EffiCarBroker"— para que el ejecutivo sienta que instaló *su* herramienta.

## What Changes

- **Backoffice instalable como PWA (installable + app shell):** se añade `manifest`, service worker y meta-tags para que Chrome/Safari ofrezcan "Agregar a pantalla de inicio". El service worker cachea el *app shell* (HTML/JS/CSS con hash de Vite) para carga rápida y arranque inmediato; **las llamadas a la API siguen requiriendo conexión** (sin offline de datos en esta iteración).
- **Identidad de app por tenant, resuelta por dominio (host-aware) desde el backend:** un endpoint público sirve `manifest.webmanifest` y los iconos según el `Host` de la petición, tomando `nombre` y `logo` del tenant. Un solo build de Vite sirve a todos los dominios; nada se provisiona por tenant en el front.
- **Iconos derivados del logo del tenant, con override futuro:** por defecto los tamaños de icono requeridos por PWA (192, 512, `maskable`, `apple-touch-icon`) se generan a partir del `logo` existente del tenant. Se deja el contrato preparado para que más adelante un tenant cargue un set de iconos dedicado sin cambiar el front.
- **Auditoría responsive incremental para móviles de 5":** se adaptan las pantallas actuales sin rediseñar flujos — navegación colapsable/bottom-nav en móvil, tablas que pasan a tarjetas, objetivos táctiles mínimos, formularios y modales usables a 320–360 px de ancho, y `viewport`/safe-areas correctos. No se rehace la arquitectura de navegación.
- **Actualización controlada de la app instalada:** estrategia de versión del service worker que evita servir un shell obsoleto tras un deploy (aviso/refresh de nueva versión).

## Capabilities

### New Capabilities
- `pwa-instalable`: El backoffice como app instalable — `manifest`, service worker de *app shell* (precache del bundle de Vite, network-first para navegación, ciclo de actualización), meta-tags y criterios de instalabilidad en Android/iOS.
- `tenant-app-identity`: Entrega host-aware del `manifest.webmanifest` e iconos por tenant desde el backend (resuelto por dominio, igual que el catálogo público), derivando nombre/iconos del tenant desde su `nombre`/`logo`, con contrato listo para un set de iconos dedicado.
- `ui-responsive-movil`: Reglas de UI/UX para que el backoffice sea plenamente operable en móviles desde 5" (~320 px): navegación adaptativa, tablas→tarjetas, objetivos táctiles, formularios/modales y viewport/safe-area.

### Modified Capabilities
<!-- Ninguna. La PWA y la responsividad son capas nuevas sobre el backoffice; no cambian los requisitos de comportamiento ya especificados (auth, rbac, navigation-menu, actas, comisiones, etc.). La resolución dominio→tenant reutiliza el patrón ya definido para el catálogo público, sin modificar aquella spec. -->

## Impact

- **Backend:**
  - Nuevo router público (sin auth) para servir la identidad de app: `GET /manifest.webmanifest` y `GET /app-icons/{size}.png` (o `icon-{size}.png` / `apple-touch-icon.png`), resolviendo el tenant por `Host`/`X-Forwarded-Host` con el mismo mecanismo del catálogo público. Si el host no está mapeado, cae a la identidad por defecto de EffiCarBroker.
  - Servicio de generación/redimensionado del icono a partir del `logo` del tenant (con `maskable` de padding seguro), cacheado; contrato preparado para override por tenant.
  - `settings.py`: mapa dominio→tenant reutilizado, identidad/colores por defecto, cache de iconos.
- **Backoffice (Vite/React):**
  - `index.html`: link a `/manifest.webmanifest`, `apple-touch-icon`, `theme-color`, `apple-mobile-web-app-*`, viewport con `viewport-fit=cover`.
  - Service worker (via `vite-plugin-pwa` o SW propio) para precache del app shell y actualización; registro en `main.tsx`; UI mínima de "hay una nueva versión".
  - Layout/nav responsive: [Layout.tsx](backoffice/src/components/Layout.tsx), [Sidebar.tsx](backoffice/src/components/Sidebar.tsx) (drawer/bottom-nav en móvil); patrón tabla→tarjetas para las páginas de listado (Vehículos, Actas, Comisiones, Órdenes de pago, Usuarios, etc.); revisión de modales (`ActaModals`, `RecepcionarModal`, `EditarActaModal`) y formularios a ≤360 px.
  - `index.css`/`tailwind.config.js`: utilidades de safe-area y breakpoints si faltan.
- **nginx:** `manifest.webmanifest` y rutas de iconos deben pasar al backend (no ser tragadas por el fallback SPA ni por la regla de assets estáticos con cache inmutable); ajustar [backoffice/nginx.prod.conf](backoffice/nginx.prod.conf).
- **Dependencias:** posible `vite-plugin-pwa` (o `workbox`) en el front; librería de imagen (p. ej. Pillow) en el backend para el redimensionado del icono.
- **Diferido (no en esta spec):** offline de datos / cola de sincronización en terreno; UI de carga de un set de iconos dedicado por tenant (solo se deja el contrato); rediseño mobile-first de flujos.
