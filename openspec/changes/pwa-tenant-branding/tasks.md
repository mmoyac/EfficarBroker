## 1. Backend — identidad de app host-aware (`tenant-app-identity`)

- [x] 1.1 **Construir** la dependency de resolución host→tenant (NO existe hoy; el `catalogo-publico` quedó diferido y sin código): `get_tenant_by_host` en `src/dependencies.py` — lee `Host`/`X-Forwarded-Host`, hace lookup `Tenant.dominio == host` (columna única, tenant `activo`), devuelve el tenant o `None` (host no mapeado → identidad por defecto, sin `404`). Sin auth. Dejarla reutilizable para el futuro `catalogo-publico`
- [x] 1.2 `settings.py`: identidad por defecto de EffiCarBroker (nombre, `theme_color`, `background_color`, icono por defecto empaquetado) y parámetros de cache de iconos (calcar patrón de `MEDIA_ROOT` ya existente)
- [x] 1.3 Añadir Pillow a `requirements.txt` (confirmado: no está)
- [x] 1.4 `src/services/app_icons.py`: `render(tenant, size, variant) -> PNG` — carga el `logo` (URL o data-URI), normaliza a cuadrado con fondo, aplica padding de zona segura para `maskable`, redimensiona; fallback al icono por defecto si no hay logo. Cache por `tenant_id`+size+variant+hash(logo); punto de extensión para un asset dedicado (prioridad sobre el logo)
- [x] 1.5 `src/routers/app_identity.py` (sin auth): `GET /manifest.webmanifest` (name/short_name = tenant.nombre, display standalone, scope/start_url `/`, colores por defecto, icons apuntando a las rutas de icono); host no mapeado → identidad por defecto
- [x] 1.6 Rutas de icono: `GET /app-icons/icon-192.png`, `/app-icons/icon-512.png`, `/app-icons/maskable-192.png`, `/app-icons/maskable-512.png`, `/app-icons/apple-touch-icon.png` (headers de cache corta/revalidable)
- [x] 1.7 Registrar el router en `main.py`; verificar CORS/headers para que Safari/Chrome pidan estas rutas al dominio del tenant
- [x] 1.8 **Resolución por subdominio del backoffice (hallazgo de topología prod):** el backoffice se sirve en `efficar-<slug>.effi4tech.cl` y la multitenancy es por JWT, no por `Tenant.dominio` (la landing .com). Añadido `Tenant.slug` (modelo + migración `0018_tenant_slug` + backfill en seed para el tenant real y demo), `APP_HOST_PREFIX`/`APP_HOST_SUFFIX` en settings, y `get_tenant_by_host` resuelve `slug` del subdominio (fallback a `dominio`). Verificado en Docker: subdominio real→tenant, inexistente→default, `.com`→tenant

## 2. Frontend — PWA instalable (`pwa-instalable`)

- [x] 2.1 Añadir `vite-plugin-pwa` (Workbox) a `backoffice` y configurarlo en `vite.config.ts` con `registerType: 'prompt'`, `injectRegister: null` (registro manual)
- [x] 2.2 Estrategias del SW: precache de assets con hash del build; navegación network-first para el documento; NetworkOnly para `/api/` y `/media/`; NO precachear `/manifest.webmanifest` ni `/app-icons/*` (host-aware del backend)
- [x] 2.3 `index.html`: `<link rel="manifest" href="/manifest.webmanifest">`, `<link rel="apple-touch-icon" href="/app-icons/apple-touch-icon.png">`, `theme-color`, `apple-mobile-web-app-capable`/`-status-bar-style`/`-title`, y `viewport` con `viewport-fit=cover`
- [x] 2.4 Registro del SW en `main.tsx` con callback de "nueva versión disponible"
- [x] 2.5 UI mínima de actualización (banner/toast "Nueva versión — Actualizar") que hace `skipWaiting` + reload al confirmar; no auto-recargar
- [ ] 2.6 SW "kill-switch" documentado/preparado para rollback (desregistrar SW y limpiar caches)

## 3. nginx / entrega

- [x] 3.1 En [backoffice/nginx.prod.conf](backoffice/nginx.prod.conf): `location = /manifest.webmanifest` y `location /app-icons/` con `proxy_pass` al backend, ubicadas ANTES de la regla de assets `immutable` y del fallback SPA; cache corta/revalidable
- [x] 3.2 Verificar en dev que `/manifest.webmanifest` y `/app-icons/*` llegan al backend (proxy de Vite o acceso directo)

## 4. Frontend — responsive incremental (`ui-responsive-movil`)

> Auditoría previa (ver design): la navegación NO es responsive (bloqueante) y hay 9 tablas crudas; los grids de tarjetas/formularios ya colapsan bien en móvil.

- [x] 4.1 Base: `viewport-fit=cover` en `index.html` (ya cubierto en 2.3) + utilidades de safe-area (`env(safe-area-inset-*)`) y, si faltan, breakpoints en `index.css`/`tailwind.config.js`; garantizar sin scroll horizontal del `body`
- [x] 4.2 **Navegación (prioridad #1):** [Layout.tsx](backoffice/src/components/Layout.tsx) — el `<aside>` fijo `w-64 h-screen` pasa a drawer off-canvas con overlay bajo `md` y botón hamburguesa en un header móvil; en `md+` se conserva el sidebar actual. Reducir `main` de `p-8` a `p-4 md:p-8`. Mantener menú por rol (`useNavigationMenu`), `TenantSwitcher` y botón de logout accesibles en el drawer. Evaluar bottom-nav para 3–4 acciones frecuentes del ejecutivo
- [x] 4.3 Tablas usables en móvil. **Hallazgo:** las 9 tablas YA estaban envueltas en `overflow-x-auto` (piso mínimo cumplido de antes) + `overflow-x:hidden` global en `body` → cero desborde de página en las 9. Tarjetas reales implementadas en [Vehiculos.tsx](backoffice/src/pages/Vehiculos.tsx) (listado primario de terreno) como patrón ejemplar (`hidden md:block` tabla + `md:hidden` tarjetas). Resto: scroll contenido (aceptable por la spec ajustada); se pueden migrar a tarjetas incrementalmente donde el uso lo pida
- [x] 4.4 Modales usables a 320–360 px ([ActaModals.tsx](backoffice/src/pages/ActaModals.tsx), [RecepcionarModal.tsx](backoffice/src/pages/RecepcionarModal.tsx), [EditarActaModal.tsx](backoffice/src/pages/EditarActaModal.tsx), [NuevaActa.tsx](backoffice/src/pages/NuevaActa.tsx)): ancho completo + scroll interno, sin recortes (los grids internos ya apilan; verificar contenedor y botones de acción)
- [x] 4.5 Objetivos táctiles ≥44 px en botones/acciones/campos primarios; revisar [Login.tsx](backoffice/src/pages/Login.tsx) y [Dashboard.tsx](backoffice/src/pages/Dashboard.tsx) en móvil

## 5. Verificación

- [x] 5.1 `tsc --noEmit` en backoffice y `py_compile`/arranque del backend en Docker
- [ ] 5.2 Lighthouse PWA sobre el build desplegado: criterio "installable" en verde
- [ ] 5.3 Prueba real de instalación en Android (Chrome) e iOS (Safari) desde DOS dominios distintos → cada uno muestra icono y nombre de su tenant
- [ ] 5.4 Prueba de actualización: nuevo deploy → aparece aviso de nueva versión y actualiza sin perder un formulario en curso
- [ ] 5.5 Revisión responsive a 320–360 px de las pantallas clave (login, listados, alta/edición de acta, recepción); sin scroll horizontal de página
- [ ] 5.6 Verificar que sin conexión abre el shell pero las vistas con datos fallan como hoy (no hay offline de datos)
