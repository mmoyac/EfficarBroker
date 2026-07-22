## ADDED Requirements

### Requirement: Backoffice instalable como PWA
El backoffice SHALL cumplir los criterios de instalabilidad de PWA en navegadores compatibles: SHALL referenciar un `manifest` válido desde el HTML, servirse sobre HTTPS en producción, registrar un service worker con `start_url` navegable, y declarar `display: standalone`, iconos de 192 y 512 px y `theme_color`/`background_color`. En Android/Chrome el navegador SHALL poder ofrecer "Agregar a pantalla de inicio"; en iOS/Safari la app SHALL ser agregable manualmente mostrando el icono correcto.

#### Scenario: Chrome ofrece instalación
- **WHEN** un ejecutivo abre el backoffice en Chrome Android sobre HTTPS
- **THEN** el navegador reconoce la app como instalable y permite "Agregar a pantalla de inicio"

#### Scenario: Auditoría de instalabilidad
- **WHEN** se ejecuta la auditoría PWA de Lighthouse sobre el backoffice desplegado
- **THEN** la app pasa el criterio "installable" (manifest válido, service worker, iconos requeridos)

### Requirement: Service worker de app shell sin cachear datos ni respuestas autenticadas
El service worker SHALL precachear el app shell (los assets con hash del build de Vite: JS, CSS y fuentes) para arranque rápido, servir las navegaciones con estrategia network-first (para no entregar un `index.html` obsoleto) y tratar toda petición bajo `/api/` y `/media/` como NetworkOnly. El service worker NO SHALL cachear respuestas de la API, datos de negocio ni contenido autenticado. La ausencia de conexión SHALL permitir abrir el app shell, pero las vistas que dependen de datos SHALL comportarse como sin PWA (requieren red).

#### Scenario: Arranque rápido desde caché del shell
- **WHEN** el usuario reabre la app instalada con el shell ya cacheado
- **THEN** la interfaz base carga desde caché sin esperar la descarga del bundle

#### Scenario: La API nunca se sirve desde caché
- **WHEN** el service worker intercepta una petición a `/api/v1/...` o `/media/...`
- **THEN** la petición va siempre a la red y su respuesta no queda cacheada

#### Scenario: Sin conexión, los datos no aparecen desde caché
- **WHEN** el dispositivo no tiene conexión y se abre la app instalada
- **THEN** el app shell se muestra pero las vistas con datos indican error/carga como sin PWA

### Requirement: Actualización controlada de la app instalada
Tras un nuevo despliegue, el sistema NO SHALL servir indefinidamente un app shell obsoleto. Cuando exista una nueva versión del service worker en espera, la app SHALL informar al usuario ("nueva versión disponible") y aplicar la actualización bajo su acción, sin recargar de forma silenciosa que pueda descartar un formulario en curso.

#### Scenario: Aviso de nueva versión
- **WHEN** hay un service worker nuevo en espera tras un deploy
- **THEN** la app muestra un aviso de actualización y actualiza al confirmarlo el usuario

#### Scenario: No se recarga en medio de una edición
- **WHEN** el usuario está completando un formulario y llega una nueva versión
- **THEN** la actualización no ocurre automáticamente hasta que el usuario la acepta
