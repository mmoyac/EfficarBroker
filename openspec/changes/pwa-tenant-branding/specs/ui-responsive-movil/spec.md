## ADDED Requirements

### Requirement: Operabilidad en móviles desde 5"
El backoffice SHALL ser plenamente operable en pantallas móviles desde ~320 px de ancho (equipos de 5") sin scroll horizontal de la página. Todo contenido que no quepa (tablas, diagramas) SHALL desplazarse dentro de su propio contenedor, nunca desbordando el `body`. El HTML SHALL declarar un `viewport` responsivo con `viewport-fit=cover` y respetar las safe-areas (`env(safe-area-inset-*)`) en dispositivos con notch/barra del sistema.

#### Scenario: Sin scroll horizontal de página
- **WHEN** se abre cualquier pantalla del backoffice a 320 px de ancho
- **THEN** la página no produce scroll horizontal; el contenido ancho se desplaza dentro de su propio contenedor

#### Scenario: Safe-area respetada
- **WHEN** la app instalada se abre en un dispositivo con notch/barra del sistema
- **THEN** los controles no quedan bajo la barra ni el notch, respetando la safe-area

### Requirement: Navegación adaptativa en móvil
La navegación principal SHALL adaptarse a móvil: bajo el breakpoint de escritorio, el sidebar fijo SHALL presentarse como un panel desplegable (drawer) accesible desde un control en el header, y las opciones de menú por rol y el cambio de tenant SHALL permanecer accesibles en esa navegación móvil. El control de navegación SHALL tener objetivos táctiles adecuados.

#### Scenario: Sidebar como drawer en móvil
- **WHEN** se abre el backoffice en un viewport móvil
- **THEN** el menú lateral no ocupa espacio fijo y se abre/cierra como panel desplegable desde el header

#### Scenario: Menú por rol accesible en móvil
- **WHEN** el usuario abre la navegación móvil
- **THEN** ve sus opciones de menú según rol y, si aplica, el cambio de automotora

### Requirement: Listados usables en móvil
Ninguna pantalla de listado SHALL provocar scroll horizontal de página en móvil: toda tabla ancha SHALL, como mínimo, quedar contenida en un contenedor con scroll propio (`overflow-x-auto`). Los listados primarios de terreno (al menos Vehículos) SHALL presentar además, en móvil, una disposición de tarjetas apiladas por registro con sus campos clave y acciones. En escritorio SHALL conservarse la tabla.

#### Scenario: Sin desborde de página en cualquier listado
- **WHEN** se abre una pantalla de listado en un viewport móvil
- **THEN** la página no produce scroll horizontal; la tabla, si no está en formato tarjeta, se desplaza dentro de su propio contenedor

#### Scenario: Listado primario en tarjetas
- **WHEN** se abre un listado primario de terreno (p. ej. Vehículos) en un viewport móvil
- **THEN** cada registro se muestra como una tarjeta con sus campos clave y acciones

#### Scenario: Tabla preservada en escritorio
- **WHEN** se abre la misma pantalla en un viewport de escritorio
- **THEN** se muestra la tabla completa como hasta ahora

### Requirement: Formularios, modales y objetivos táctiles en móvil
En móvil, los modales y formularios (por ejemplo alta/edición de acta, recepción, edición) SHALL ser usables a 320–360 px: ocupar el ancho disponible con scroll interno cuando el contenido excede el alto, sin recortar campos ni botones. Los elementos interactivos primarios (botones, enlaces de acción, campos) SHALL tener un objetivo táctil de al menos 44×44 px.

#### Scenario: Modal usable a 360 px
- **WHEN** se abre un modal de edición en un viewport de 360 px
- **THEN** el modal ocupa el ancho disponible, permite scroll interno y no recorta campos ni botones

#### Scenario: Objetivos táctiles suficientes
- **WHEN** el usuario interactúa con botones y campos en móvil
- **THEN** cada objetivo interactivo primario mide al menos 44×44 px
