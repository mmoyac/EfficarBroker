## Why

Hoy la ficha del auto solo tiene datos duros (PPU, marca, año, N° motor…): no hay forma de cargar las **fotografías ni el video 360** que la automotora ya produce para cada publicación. Ese material es lo que vende el auto y es exactamente lo que necesitará la landing pública para el catálogo. Sin un lugar donde guardarlo y una API que lo exponga, administración/operaciones no puede completar la publicación ni preparar el terreno para la landing.

## What Changes

- **Galería asociada al acta (publicación), no al vehículo:** cada recepción/publicación tiene su propio set de fotos y su video. Consistente con la doctrina de entidad fuerte (las fotos son material de *esa* publicación); al re-consignar el auto con otro dueño, se cargan fotos nuevas sin pisar el historial anterior.
- **Galería libre con una foto principal:** N fotos ordenables, una marcada como `es_principal` (la imagen grande del ejemplo). Sin cantidad fija de campos.
- **Doble vía de ingreso de imágenes:** administración puede **pegar una URL del cloud** (las que ya viven en WordPress, p. ej. `https://vendemostuautomovil.com/wp-content/uploads/.../DSC04716-1024x683.jpg`) **o subir un archivo** a un storage propio del backend, que devuelve la URL servible. Ambas terminan como una fila de foto con su URL.
- **Video 360 por enlace de YouTube:** un campo de URL de YouTube en el acta (p. ej. `https://youtu.be/cYiwenPy3Hw`), normalizado y validado como enlace de YouTube; el frontend deriva el embed/thumbnail.
- **Edición en backoffice por administración/operaciones:** `Management`/`TenantAdmin`/`SuperAdmin` gestionan la galería y el video del acta activa desde la ficha de vehículo; cada mutación se audita. (Se evalúa permitir también al captador/vendedor de la propia acta mientras no esté cerrada — se decide en design.)
- **Transición Publicar/Despublicar (activa el estado `PUBLICADO`):** una acción "Publicar" mueve el acta de `RECEPCIONADO` a `PUBLICADO` — el momento en que el auto se sube a los portales para muestra a clientes — y exige tener al menos una foto cargada. "Despublicar" la devuelve a `RECEPCIONADO`. Esto da uso al estado `PUBLICADO`, que hasta ahora existía en el catálogo pero sin ninguna transición que lo alcanzara. La venta sigue siendo posible desde `PUBLICADO` o directo desde `RECEPCIONADO` (venta rápida sin publicar).
- **Endpoint público de lectura listo para la landing:** `GET` sin autenticación que resuelve `tenant_id` por dominio/host y devuelve, para los autos **publicados**, su ficha + galería + video. Deja la landing futura conectada sin tocar el backend de nuevo.
- **Storage de archivos:** se introduce almacenamiento de medios (directorio servido por el backend, con volumen persistente en Docker), diseñado para poder migrar a S3/objeto sin cambiar el contrato de la API.

## Capabilities

### New Capabilities
- `galeria-multimedia`: Fotos (galería ordenable con una principal, por URL del cloud o archivo subido) y video 360 de YouTube asociados al acta; su modelo de datos, storage, endpoints autenticados de gestión y reglas de permisos/auditoría.
- `catalogo-publico`: Endpoint público (sin auth) que resuelve el tenant por dominio y expone los vehículos publicados con su galería y video para la landing.

### Modified Capabilities
<!-- Ninguna: la galería es material nuevo colgado del acta; no cambia el comportamiento especificado de acta-recepcion, derivacion-venta ni registro-venta. -->

## Impact

- **Base de datos:** nuevas tablas operacionales `acta_fotos` (`acta_id`, `url`, `orden`, `es_principal`, `origen`, timestamps) y campo `video_youtube_url` en `actas_recepcion`; índice único parcial de una sola foto principal por acta. Catálogo `origenes_foto` (`URL_CLOUD`, `ARCHIVO`) por la regla de "todo enum es catálogo".
- **Backend:** nuevo `src/models/multimedia.py` (o extensión de `acta.py`); `src/routers/multimedia.py` para gestión autenticada; `src/routers/public.py` para lectura pública; `src/services/storage.py` para subida/servido de archivos; `settings.py` gana `MEDIA_ROOT`, `MEDIA_URL_BASE` y `PUBLIC_TENANT_HOST_MAP`; `main.py` monta estáticos y el router público.
- **APIs:** `GET/POST/PATCH/DELETE /api/v1/actas/{acta_id}/fotos`, `POST /api/v1/actas/{acta_id}/fotos/upload`, `PATCH /api/v1/actas/{acta_id}/video`; y público `GET /api/v1/public/vehiculos` + `GET /api/v1/public/vehiculos/{id}` (resuelto por header/host).
- **Backoffice:** la ficha de vehículo ([Vehiculos.tsx](backoffice/src/pages/Vehiculos.tsx)) gana una sección de galería (grilla ordenable, marcar principal, subir/pegar URL, eliminar) y el campo de video; nuevos servicios/tipos en [vehiculos.ts](backoffice/src/services/vehiculos.ts).
- **Docker:** volumen para `MEDIA_ROOT` en `docker-compose.yml`.
- **Seed:** catálogo `origenes_foto`; opcionalmente algunas fotos/video demo para el auto sembrado.
- **Diferido:** la app Next.js de la landing (`landing/vendemostuautomovil/`) que consume el endpoint público se construye aparte; aquí solo se deja el contrato listo.
