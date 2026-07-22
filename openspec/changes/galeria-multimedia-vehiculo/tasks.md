## 1. Modelo y migración

- [x] 1.1 Catálogo `origenes_foto` (`URL_CLOUD`, `ARCHIVO`) en `src/models/catalogs.py`
- [x] 1.2 Operacional `ActaFoto` (`tenant_id`, `acta_id` FK→`actas_recepcion` ON DELETE CASCADE, `url`, `orden`, `es_principal`, `origen_id`, timestamps) en `src/models/acta.py`
- [x] 1.3 Columna `video_youtube_url` (nullable) en `ActaRecepcion` + relación `fotos` (order_by `orden`)
- [x] 1.4 Migración Alembic 0014: catálogo, tabla `acta_fotos`, columna `video_youtube_url`, e índice único parcial `UNIQUE (acta_id) WHERE es_principal`
- [x] 1.5 Seed: sembrar `origenes_foto` (galería/video demo omitidos — opcionales)

## 2. Storage de archivos

- [x] 2.1 `settings.py`: `MEDIA_ROOT`, `MEDIA_URL_BASE`, `MEDIA_MAX_BYTES`, tipos MIME permitidos
- [x] 2.2 `src/services/storage.py`: `save(tenant_id, content, ext) -> url` y `delete(url)`; filesystem `MEDIA_ROOT/<tenant_id>/<uuid>.<ext>`
- [x] 2.3 Montar `StaticFiles` en `MEDIA_URL_BASE` desde `main.py`
- [x] 2.4 Volumen `media` para `MEDIA_ROOT` en `docker-compose.yml`

## 3. Backend — gestión de galería (autenticada)

- [x] 3.1 Schemas Pydantic strict: `FotoOut`, `FotoUrlIn`, `FotoUpdateIn` (orden/principal), `VideoIn`
- [x] 3.2 `src/routers/multimedia.py`: `GET /actas/{acta_id}/fotos` (galería ordenada)
- [x] 3.3 `POST /actas/{acta_id}/fotos` (por URL del cloud, valida http(s), `origen = URL_CLOUD`); primera foto → principal por defecto
- [x] 3.4 `POST /actas/{acta_id}/fotos/upload` (multipart, valida tipo/tamaño, guarda vía storage, `origen = ARCHIVO`)
- [x] 3.5 `PATCH /actas/{acta_id}/fotos/{foto_id}` (reordenar y marcar principal, desmarcando la anterior en la misma transacción)
- [x] 3.6 `DELETE /actas/{acta_id}/fotos/{foto_id}` (si `origen = ARCHIVO` → `storage.delete`; reasignar principal si se borró la principal)
- [x] 3.7 `PATCH /actas/{acta_id}/video` (valida/normaliza YouTube; vacío/null borra) — util `src/utils/youtube.py`
- [x] 3.8 Guardas de permiso: transversales siempre; captador/vendedor/equipo derivada solo si `cerrada = false`; `403` en otro caso; `404` si el acta es de otro tenant
- [x] 3.9 Auditoría en cada mutación (`entidad="acta_foto"`/`"acta_video"`, actor, acción)
- [x] 3.10 Registrar el router en `main.py`; exponer `video_youtube_url` y `captador_user_id` en el detalle del acta

## 4. Backend — endpoint público (DIFERIDO — capacidad `catalogo-publico`)

- [ ] 4.1 Dependency `get_public_tenant` (resuelve tenant por `Host`/`X-Forwarded-Host` contra el mapa; `404` si no mapeado; override por header solo en DEBUG)
- [ ] 4.2 Schemas públicos sin datos sensibles: `PublicVehiculoItem`, `PublicVehiculoDetail`, `PublicFoto`
- [ ] 4.3 `GET /api/v1/public/vehiculos` (solo actas activas `PUBLICADO`/`CON_VISITA_PROGRAMADA` del tenant; incluye foto principal y video)
- [ ] 4.4 `GET /api/v1/public/vehiculos/{id}` (detalle con galería completa + video; `404` si no publicado o de otro tenant)
- [ ] 4.5 `src/routers/public.py` sin auth, registrado en `main.py`; agregar el origen de la landing a CORS

## 5. Backoffice

- [x] 5.1 Tipos y servicios en `src/services/actas.ts` (listar/crear/subir/patch/eliminar fotos, patch video) + helper `assetUrl` en `api.ts`
- [x] 5.2 Sección "Galería" en `ActaDetalle.tsx`: grilla de miniaturas reordenable, marcar principal, subir archivo y pegar URL, eliminar, con preview
- [x] 5.3 Campo de video YouTube con validación y preview del thumbnail
- [x] 5.4 Mostrar galería y video solo-lectura para roles sin permiso de edición; ocultar acciones según permiso

## 6. Publicar / Despublicar (DIFERIDO — decidido con el usuario)

- [ ] 6.1 `POST /actas/{id}/publicar` (RECEPCIONADO→PUBLICADO, exige ≥1 foto) y `POST /actas/{id}/despublicar`
- [ ] 6.2 Acción Publicar/Despublicar en el backoffice

## 7. Verificación

- [x] 7.1 Chequeo de sintaxis backend (py_compile) y de tipos frontend (`tsc --noEmit`)
- [ ] 7.2 Migración aplicada en Docker + smoke de arranque del backend
- [ ] 7.3 Prueba end-to-end: cargar 1 principal + 4 fotos + video 360 en un acta y verlas
