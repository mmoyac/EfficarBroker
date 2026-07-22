## ADDED Requirements

### Requirement: Galería de fotos asociada al acta
El sistema SHALL modelar las fotos de un vehículo como filas operacionales `acta_fotos` asociadas al **acta de recepción** (no al vehículo), con `tenant_id`, `acta_id`, `url`, `orden`, `es_principal`, `origen_id` (catálogo) y timestamps. Un acta SHALL admitir N fotos ordenables. Al re-consignarse el mismo vehículo en un acta nueva, la galería de la recepción anterior SHALL conservarse intacta y la nueva recepción SHALL partir con su propia galería vacía.

#### Scenario: Cargar varias fotos en un acta
- **WHEN** administración agrega tres fotos a un acta publicada
- **THEN** el acta expone las tres fotos con su `orden`, y la galería de recepciones anteriores del mismo vehículo no se altera

#### Scenario: Reconsignación no pisa fotos previas
- **WHEN** un vehículo con galería en un acta cerrada se recepciona en un acta nueva
- **THEN** la nueva acta parte sin fotos y la galería del acta anterior sigue consultable

### Requirement: Una sola foto principal por acta
El sistema SHALL garantizar que como máximo una foto por acta tenga `es_principal = true`, mediante un índice único parcial. Al marcar una foto como principal, la que estuviera marcada SHALL dejar de serlo en la misma operación. La foto principal SHALL usarse como imagen destacada (grande) y las demás como miniaturas ordenadas por `orden`.

#### Scenario: Marcar una nueva principal
- **WHEN** existe una foto principal y administración marca otra como principal
- **THEN** la anterior deja de ser principal y solo la nueva queda marcada

#### Scenario: Primera foto es principal por defecto
- **WHEN** se agrega la primera foto de un acta sin principal previa
- **THEN** esa foto queda marcada como principal automáticamente

### Requirement: Ingreso por URL del cloud
El sistema SHALL permitir registrar una foto entregando una URL http(s) ya existente en el cloud. La foto resultante SHALL tener `origen = URL_CLOUD` y almacenar la URL tal cual (validada como http(s)). El sistema SHALL rechazar URLs vacías o con esquema distinto de http/https con `400`.

#### Scenario: Pegar URL de WordPress
- **WHEN** administración pega `https://vendemostuautomovil.com/wp-content/uploads/2026/07/DSC04716-1024x683.jpg`
- **THEN** se crea una foto con esa URL y `origen = URL_CLOUD`

#### Scenario: URL inválida
- **WHEN** se envía una cadena que no es una URL http(s)
- **THEN** el sistema responde `400` y no crea la foto

### Requirement: Ingreso por archivo subido
El sistema SHALL permitir subir un archivo de imagen (JPEG/PNG/WebP) a un storage propio del backend, que SHALL generar y persistir una URL servible. La foto resultante SHALL tener `origen = ARCHIVO`. El sistema SHALL validar el tipo de contenido y rechazar tipos no soportados o tamaños sobre el límite configurado con `400`/`413`. Los archivos SHALL guardarse aislados por tenant.

#### Scenario: Subida válida
- **WHEN** administración sube un archivo JPEG de 2 MB
- **THEN** el backend lo almacena, genera una URL servible y crea la foto con `origen = ARCHIVO`

#### Scenario: Tipo no soportado
- **WHEN** se sube un archivo que no es imagen soportada (p. ej. PDF)
- **THEN** el sistema responde `400` y no almacena el archivo

### Requirement: Video 360 por enlace de YouTube
El acta SHALL tener un campo opcional `video_youtube_url`. El sistema SHALL aceptar solo URLs de YouTube (`youtube.com/watch?v=…`, `youtu.be/…` o `youtube.com/shorts/…`), normalizarlas y validarlas; una URL de otro dominio SHALL responder `400`. Enviar `null` o vacío SHALL borrar el video del acta.

#### Scenario: Guardar enlace corto
- **WHEN** administración guarda `https://youtu.be/cYiwenPy3Hw`
- **THEN** el acta persiste el enlace y la ficha puede derivar el embed/thumbnail

#### Scenario: Enlace que no es de YouTube
- **WHEN** se envía una URL de otro dominio
- **THEN** el sistema responde `400`

#### Scenario: Quitar el video
- **WHEN** administración envía el video vacío en un acta que tenía enlace
- **THEN** el acta queda sin `video_youtube_url`

### Requirement: Gestión restringida y auditada
El sistema SHALL restringir crear, reordenar, marcar principal, eliminar fotos y editar el video a `Management`/`TenantAdmin`/`SuperAdmin`, o al captador/vendedor de la propia acta mientras esta no esté cerrada. Un rol no autorizado SHALL recibir `403`. Toda mutación de la galería o del video SHALL registrar una fila en `logs_auditoria` con el actor, el `acta_id` y la acción. Todas las operaciones SHALL filtrar por el `tenant_id` del usuario; un acta de otro tenant SHALL responder `404`.

#### Scenario: Administración edita la galería
- **WHEN** un usuario `Management` agrega y reordena fotos de un acta de su tenant
- **THEN** los cambios se persisten y quedan auditados

#### Scenario: Rol no autorizado
- **WHEN** un usuario `Sales` que no es captador ni vendedor del acta intenta borrar una foto
- **THEN** el sistema responde `403`

#### Scenario: Aislamiento por tenant
- **WHEN** un usuario intenta gestionar fotos de un acta de otro tenant
- **THEN** el sistema responde `404`

### Requirement: Publicar y despublicar el auto
Publicar es el evento en que el auto se sube a los portales para muestra a clientes; requiere material visual. El sistema SHALL exponer `POST /api/v1/actas/{id}/publicar` que transita el acta de `RECEPCIONADO` a `PUBLICADO`, y `POST /api/v1/actas/{id}/despublicar` que la devuelve de `PUBLICADO` a `RECEPCIONADO`. Publicar SHALL exigir que el acta tenga al menos una foto en su galería; si no la tiene, SHALL responder `409`. Ambas transiciones SHALL estar restringidas a `Management`/`TenantAdmin`/`SuperAdmin` (o al captador/vendedor de la propia acta mientras no esté cerrada), registrar historial de estado y auditoría, y scopearse al tenant. La venta SHALL seguir siendo posible tanto desde `PUBLICADO` como directamente desde `RECEPCIONADO` (venta rápida sin publicar).

#### Scenario: Publicar con fotos
- **WHEN** un usuario autorizado publica un acta en `RECEPCIONADO` que tiene al menos una foto
- **THEN** el acta pasa a `PUBLICADO`, se registra el historial y queda visible para el catálogo público

#### Scenario: Publicar sin fotos
- **WHEN** se intenta publicar un acta que no tiene ninguna foto en su galería
- **THEN** el sistema responde `409` indicando que se requiere material visual

#### Scenario: Despublicar
- **WHEN** un usuario autorizado despublica un acta en `PUBLICADO`
- **THEN** el acta vuelve a `RECEPCIONADO` y deja de aparecer en el catálogo público

#### Scenario: Publicar desde un estado inválido
- **WHEN** se intenta publicar un acta que no está en `RECEPCIONADO` (por ejemplo `CAPTADO` o `VENDIDO`)
- **THEN** el sistema responde `409`

#### Scenario: Venta directa sin publicar
- **WHEN** se registra la venta de un acta en `RECEPCIONADO` sin haberla publicado
- **THEN** la venta se acepta (publicar es opcional para vender)

### Requirement: Catálogo de orígenes de foto
El sistema SHALL modelar el origen de la foto como catálogo `origenes_foto` con al menos `URL_CLOUD` y `ARCHIVO`, referenciado por FK desde `acta_fotos`, sembrado por seed. Ningún valor de origen SHALL quedar como literal en código.

#### Scenario: Orígenes sembrados
- **WHEN** se consulta el catálogo de orígenes tras el seed
- **THEN** existen al menos `URL_CLOUD` y `ARCHIVO`
