## ADDED Requirements

### Requirement: Resolución de tenant por dominio
El endpoint público SHALL resolver el `tenant_id` a partir del host de la petición (dominio de la landing) mediante un mapa configurable dominio→tenant. Si el host no está mapeado a ningún tenant, el sistema SHALL responder `404`. Ninguna consulta pública SHALL devolver datos de un tenant distinto al resuelto.

#### Scenario: Dominio conocido
- **WHEN** llega una petición pública con host `vendemostuautomovil.com`
- **THEN** el sistema resuelve el tenant correspondiente y responde solo con sus datos

#### Scenario: Dominio no mapeado
- **WHEN** llega una petición pública desde un host sin tenant asociado
- **THEN** el sistema responde `404`

### Requirement: Listado público de vehículos publicados
El sistema SHALL exponer `GET /api/v1/public/vehiculos` sin autenticación, que devuelve, para el tenant resuelto por dominio, solo los vehículos cuya acta activa esté en estado `PUBLICADO` (o `CON_VISITA_PROGRAMADA`). Cada elemento SHALL incluir la ficha pública (marca, modelo, versión, año, color, combustible, precio pactado), la foto principal y el enlace de video si existe. Autos sin acta publicada NO SHALL aparecer.

#### Scenario: Solo publicados
- **WHEN** el tenant tiene autos en `RECEPCIONADO`, `PUBLICADO` y `VENDIDO`
- **THEN** el listado público solo incluye los `PUBLICADO` (y `CON_VISITA_PROGRAMADA`)

#### Scenario: Elemento con foto principal
- **WHEN** un auto publicado tiene galería con foto principal
- **THEN** el elemento del listado expone la URL de la foto principal

### Requirement: Detalle público de un vehículo publicado
El sistema SHALL exponer `GET /api/v1/public/vehiculos/{id}` sin autenticación, que devuelve la ficha pública del auto publicado del tenant resuelto, con su galería completa (fotos ordenadas, principal marcada) y el `video_youtube_url`. Si el id no corresponde a un auto publicado de ese tenant, SHALL responder `404`. La respuesta pública NO SHALL incluir datos sensibles (dueño, RUT, N° motor/chasis, comisiones, sucursal interna).

#### Scenario: Detalle con galería y video
- **WHEN** se pide el detalle público de un auto publicado con 5 fotos y video
- **THEN** la respuesta incluye las 5 fotos ordenadas con la principal marcada y el enlace de YouTube

#### Scenario: Auto no publicado
- **WHEN** se pide el detalle público de un auto no publicado o de otro tenant
- **THEN** el sistema responde `404`

#### Scenario: Sin datos sensibles
- **WHEN** se consulta cualquier respuesta pública
- **THEN** no aparecen dueño, RUT, N° motor/chasis, comisiones ni datos internos de sucursal
