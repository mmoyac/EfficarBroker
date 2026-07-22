## Context

`vehiculos` es entidad fuerte (solo identidad física); todo lo circunstancial —dueño, estado, publicación, venta— vive en `actas_recepcion`. La publicación (`PUBLICADO`) es un estado del acta. El material de marketing (fotos y video) es propio de *esa* publicación, por lo que cuelga del acta, no del vehículo.

Estado actual relevante:
- No existe storage de archivos: el único binario que produce el backend es el PDF del acta, generado en memoria y devuelto en la respuesta ([acta_pdf.py](backend/src/services/acta_pdf.py)); los logos del tenant se guardan como data-URI. No hay `StaticFiles` montado en [main.py](backend/src/main.py).
- No hay endpoints públicos: todo cuelga de `/api/v1` con auth JWT y `get_effective_tenant_id`.
- La ficha se edita en [Vehiculos.tsx](backoffice/src/pages/Vehiculos.tsx) vía `PATCH /vehiculos/{id}`, restringido de forma escalonada.
- La landing (`landing/vendemostuautomovil/`) aún no existe; `project.md` la contempla resolviendo `tenant_id` por dominio.

Restricciones duras del proyecto: todo enum es catálogo; multitenancy no negociable; auditoría append-only por mutación; Pydantic strict; API `/api/v1/`.

## Goals / Non-Goals

**Goals:**
- Guardar N fotos por acta (URL del cloud o archivo subido) con una principal, y un enlace de video YouTube.
- Storage de archivos propio, aislado por tenant, con contrato de URL estable y swappable a S3 después.
- Endpoint público de lectura por dominio→tenant que exponga los autos publicados con su galería y video, sin datos sensibles.
- Gestión en backoffice para administración/operaciones, auditada.

**Non-Goals:**
- Construir la app Next.js de la landing (se hace aparte; aquí solo el contrato de API).
- Procesamiento de imágenes (thumbnails, recorte, EXIF, watermark). Se guarda tal cual se sube.
- Migrar a S3/CDN ahora (se deja la abstracción, no la implementación).
- Alojar el video: solo se guarda el enlace de YouTube; el embed lo hace el frontend.

## Decisions

### 1. Las fotos cuelgan del acta (`acta_fotos`), no del vehículo
Tabla operacional `acta_fotos(id, tenant_id, acta_id FK→actas_recepcion ON DELETE CASCADE, url, orden, es_principal, origen_id FK→origenes_foto, created_at, updated_at)`. Video como columna `video_youtube_url` en `actas_recepcion`.
- **Por qué:** consistente con la doctrina de entidad fuerte y con `acta_checklist`/`acta_estado_historial`; permite historial de galerías por recepción sin pisarse.
- **Alternativa descartada:** colgar del vehículo — más simple pero mezcla el material de dos consignaciones distintas del mismo auto y contradice el resto del modelo.

### 2. Una principal garantizada por índice único parcial
`CREATE UNIQUE INDEX ... ON acta_fotos (acta_id) WHERE es_principal` (mismo patrón que el acta activa por vehículo). Marcar una nueva principal desmarca la anterior en la misma transacción. La primera foto de un acta se marca principal por defecto.
- **Por qué:** la invariante no puede depender solo del router (requests concurrentes), igual que el índice parcial de acta activa existente.

### 3. `origen` como catálogo `origenes_foto`
Catálogo con `URL_CLOUD` y `ARCHIVO`, FK desde `acta_fotos`, sembrado por seed.
- **Por qué:** regla dura "todo enum es catálogo". Distingue en la UI/limpieza qué fotos tienen archivo físico propio (borrables del storage) vs. URLs externas.

### 4. Storage local abstraído tras un servicio
`src/services/storage.py` con interfaz mínima `save(tenant_id, filename, content) -> url` y `delete(url)`. Implementación inicial: filesystem bajo `MEDIA_ROOT/<tenant_id>/<uuid>.<ext>`, servido por `StaticFiles` montado en `MEDIA_URL_BASE` (p. ej. `/media`). Config nueva en [settings.py](backend/src/config/settings.py): `MEDIA_ROOT`, `MEDIA_URL_BASE`, `MEDIA_MAX_BYTES`, tipos permitidos. Volumen en `docker-compose.yml` para persistir `MEDIA_ROOT`.
- **Por qué:** MVP sin dependencias de nube; el contrato (guardar bytes → URL) es idéntico al de S3, así que migrar después es cambiar la implementación del servicio, no la API ni el modelo.
- **Alternativa descartada:** guardar el binario en la BD (bloat, backups pesados) o data-URI como los logos (no escala a galerías).
- **Trade-off:** el bind mount `./backend:/app` en dev basta; en prod el volumen debe ser persistente y respaldado. Las URLs de archivo son relativas al backend hasta que exista CDN.

### 5. Endpoint público resuelto por host, router separado
`src/routers/public.py` (sin `Depends(get_current_user)`), montado bajo `/api/v1/public`. Resuelve tenant con un dependency `get_public_tenant` que lee el host (`Host`/`X-Forwarded-Host`) contra un mapa configurable `PUBLIC_TENANT_HOST_MAP` (dominio→tenant slug/id). Devuelve solo autos cuya acta activa esté `PUBLICADO`/`CON_VISITA_PROGRAMADA`, con schemas públicos dedicados (sin dueño, RUT, N° motor/chasis, comisiones, sucursal).
- **Por qué:** aísla la superficie sin auth en un router propio, con sus propios schemas de salida, evitando filtrar campos sensibles por accidente. Resolver por host es lo que ya prevé `project.md` para "una landing por tenant".
- **Alternativa descartada:** un query param `?tenant=` — frágil y ligado a IDs internos; el dominio es la fuente natural en producción. En dev se permite override por header para pruebas.
- **CORS:** el origen de la landing se agrega a `BACKEND_CORS_ORIGINS`.

### 6. Endpoints de gestión bajo el acta
`GET/POST/DELETE /api/v1/actas/{acta_id}/fotos`, `PATCH .../fotos/{foto_id}` (orden/principal), `POST .../fotos/upload` (multipart), `PATCH /api/v1/actas/{acta_id}/video`. Permisos: transversales (`Management`/`TenantAdmin`/`SuperAdmin`) siempre; captador/vendedor de la propia acta solo si `cerrada = false`. Reutiliza `audit_service.log` con `entidad="acta_foto"`/`"acta_video"`.
- **Por qué:** el recurso vive bajo su acta, coherente con el resto del módulo. Permitir al captador editar mientras no esté cerrada evita cuellos de botella en administración para autos aún en gestión.

### 7. Validación de YouTube en backend
Normalizar a una forma canónica y extraer el `video_id` con regex de los patrones `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`. Rechazar otros dominios con `400`. Guardar la URL normalizada; el frontend deriva embed/thumbnail (`https://img.youtube.com/vi/<id>/hqdefault.jpg`).

## Risks / Trade-offs

- **[Storage local no escala horizontalmente]** → Varias réplicas del backend no comparten filesystem local. Mitigación: el servicio de storage está abstraído; en prod multi-réplica se cambia a S3 sin tocar modelo ni API. Para el MVP (una réplica) es suficiente.
- **[Superficie pública sin auth filtra datos]** → Mitigación: router aislado con schemas de salida propios que solo contienen campos públicos; tests que verifican ausencia de dueño/RUT/N° motor/comisiones.
- **[Borrado de fotos deja archivos huérfanos]** → Mitigación: al eliminar una foto `origen = ARCHIVO`, el router llama `storage.delete(url)`; las `URL_CLOUD` no se tocan (no son nuestras). El `ON DELETE CASCADE` borra filas al borrar el acta, pero no los binarios: se documenta como limpieza diferida.
- **[Resolución por host en dev/proxy]** → Detrás de proxy el `Host` real llega en `X-Forwarded-Host`. Mitigación: el dependency contempla ambos y admite un header de override solo cuando `DEBUG`.
- **[Imágenes muy pesadas]** → Sin procesamiento, una foto grande se sirve tal cual. Mitigación: límite `MEDIA_MAX_BYTES`; el thumbnailing queda para una iteración futura si hace falta.

## Migration Plan

1. Migración Alembic (posterior a la última de `comisiones-ejecutivo`): catálogo `origenes_foto`, tabla `acta_fotos` con índice único parcial de principal, columna `video_youtube_url` en `actas_recepcion`.
2. Seed: sembrar `origenes_foto`; opcionalmente cargar la galería/video demo del auto sembrado (URLs del cloud, sin subir archivos).
3. `MEDIA_ROOT` y volumen: crear el directorio y el volumen Docker antes del deploy; en dev se crea al primer upload.
4. Rollback: la migración es aditiva (nuevas tablas/columna); revertir = drop de `acta_fotos`, del catálogo y de la columna. Los archivos en `MEDIA_ROOT` se limpian aparte.

## Open Questions

- ¿El mapa dominio→tenant se configura por env (`PUBLIC_TENANT_HOST_MAP`) o pasa a ser un campo en la maestra `tenants` (p. ej. `dominio_publico`)? Preferencia: campo en `tenants` para que sea administrable, pero se puede arrancar por env y migrar. **A decidir en apply.**
- ¿El listado público necesita paginación/filtros (marca, precio) desde ya, o basta el listado completo de publicados para la primera landing? Se asume listado simple ahora.
- ¿Límite de fotos por acta (p. ej. 15) o libre? Se asume libre con tope alto configurable.
