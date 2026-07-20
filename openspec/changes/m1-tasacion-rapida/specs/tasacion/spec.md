## ADDED Requirements

### Requirement: Tasación rápida por PPU y kilometraje
El sistema SHALL exponer una tasación rápida que reciba PPU y kilometraje y retorne tres umbrales de precio: mercado, retoma y publicación sugerido.

#### Scenario: Simulación exitosa
- **WHEN** un usuario autorizado envía una PPU válida y kilometraje válido a `POST /api/v1/tasacion/simular`
- **THEN** el sistema responde `200` con `precio_mercado`, `precio_retoma` y `precio_publicacion_sugerido`

#### Scenario: Datos inválidos
- **WHEN** se envía kilometraje negativo o PPU fuera de largo permitido
- **THEN** el sistema responde `422`

### Requirement: Control de acceso para tasación
La tasación rápida SHALL requerir autenticación y autorización por rol.

#### Scenario: Rol permitido
- **WHEN** un usuario con rol `Sales`/`Management`/`TenantAdmin` invoca `POST /api/v1/tasacion/simular`
- **THEN** el sistema permite la operación

#### Scenario: Rol no permitido
- **WHEN** un usuario con rol no autorizado invoca `POST /api/v1/tasacion/simular`
- **THEN** el sistema responde `403`

### Requirement: Backoffice con vista de tasación
El backoffice SHALL ofrecer la ruta `/tasacion` con formulario de PPU y kilometraje y visualización de los tres precios de salida.

#### Scenario: Uso desde UI
- **WHEN** el ejecutivo completa el formulario de `/tasacion` y lo envía
- **THEN** la UI muestra los tres precios en pantalla sin redirigir a otra sección

### Requirement: Etapa M1 parcial declarada
Mientras no exista integración externa ni persistencia operacional, la implementación SHALL declarar explícitamente que la fuente actual es simulación interna.

#### Scenario: Transparencia de fuente
- **WHEN** la UI muestra el resultado de tasación
- **THEN** incluye una indicación de que el cálculo proviene de simulación interna
