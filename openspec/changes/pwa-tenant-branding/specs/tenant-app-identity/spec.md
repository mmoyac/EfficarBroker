## ADDED Requirements

### Requirement: Manifest host-aware resuelto por dominio
El sistema SHALL exponer `GET /manifest.webmanifest` sin autenticación, resolviendo el tenant a partir del host de la petición (`Host`/`X-Forwarded-Host`). El manifest devuelto SHALL usar el `nombre` del tenant como `name`/`short_name`, y sus `icons` SHALL apuntar a las rutas de icono host-aware del backend. Si el host no está mapeado a ningún tenant, el sistema SHALL devolver un manifest con la identidad por defecto de EffiCarBroker (no un error), de modo que la app siga siendo instalable. El manifest NO SHALL exponer datos de un tenant distinto al resuelto por el host.

La resolución host→tenant SHALL contemplar la topología real de despliegue: el backoffice se sirve por tenant en el subdominio `<prefix><slug><suffix>` (p. ej. `efficar-<slug>.effi4tech.cl`), y la multitenancy de la app es por JWT, no por `Tenant.dominio`. Por tanto el sistema SHALL resolver el tenant extrayendo el `slug` del subdominio del backoffice y buscándolo en el tenant; SHALL además admitir el match directo por `Tenant.dominio` (dominio público de la landing) para uso futuro.

#### Scenario: Subdominio de backoffice de un tenant
- **WHEN** se pide `/manifest.webmanifest` con host `efficar-<slug>.effi4tech.cl` de una automotora
- **THEN** el manifest devuelve el nombre de esa automotora y apunta a sus iconos

#### Scenario: Dominio público de la landing
- **WHEN** se pide `/manifest.webmanifest` con el dominio público (`.com`) de una automotora
- **THEN** el manifest resuelve el mismo tenant por `Tenant.dominio`

#### Scenario: Host no mapeado
- **WHEN** se pide `/manifest.webmanifest` desde un host sin tenant asociado
- **THEN** el manifest devuelve la identidad por defecto de EffiCarBroker y la app sigue siendo instalable

### Requirement: Iconos de app derivados del logo del tenant
El sistema SHALL exponer rutas de icono sin autenticación (tamaños 192 y 512, variante `maskable`, y `apple-touch-icon`) que resuelven el tenant por host y devuelven un PNG cuadrado derivado del `logo` del tenant, normalizado a fondo seguro y con zona segura de padding para la variante `maskable`. Si el tenant no tiene `logo`, el sistema SHALL devolver el icono por defecto de EffiCarBroker. Los iconos generados SHALL cachearse por tenant y tamaño e invalidarse cuando cambie el logo del tenant.

#### Scenario: Icono desde el logo del tenant
- **WHEN** se pide el icono de 512 px para un dominio cuyo tenant tiene `logo`
- **THEN** el backend devuelve un PNG cuadrado de 512 px derivado de ese logo

#### Scenario: Variante maskable con zona segura
- **WHEN** se pide la variante `maskable` de un icono
- **THEN** el PNG incluye padding de zona segura para que no se recorte el logo al aplicarse la máscara

#### Scenario: Tenant sin logo
- **WHEN** el tenant resuelto no tiene `logo` cargado
- **THEN** el backend devuelve el icono por defecto de EffiCarBroker

### Requirement: Identidad de app correcta por dominio en la app instalada
Instalar el backoffice desde el dominio de un tenant SHALL producir en el dispositivo un icono y nombre correspondientes a ese tenant, y hacerlo desde el dominio de otro tenant SHALL producir icono y nombre distintos, a pesar de servirse el mismo build de frontend. En iOS, el icono de pantalla de inicio SHALL resolverse mediante el `apple-touch-icon` del HTML apuntando a la ruta host-aware del backend.

#### Scenario: Dos dominios, dos identidades
- **WHEN** un usuario instala la app desde el dominio del tenant A y otro desde el dominio del tenant B
- **THEN** cada pantalla de inicio muestra el icono y nombre de su respectivo tenant

#### Scenario: Icono correcto en iOS
- **WHEN** un usuario en Safari iOS agrega la app a la pantalla de inicio desde el dominio de su tenant
- **THEN** el icono mostrado es el de ese tenant, resuelto desde `apple-touch-icon` del backend

### Requirement: Contrato preparado para un set de iconos dedicado por tenant
El contrato de las rutas de icono SHALL permitir a futuro que un tenant use un set de iconos dedicado en lugar del derivado del logo, sin cambiar las URLs consumidas por el manifest ni el HTML. Cuando exista un asset de icono dedicado para el tenant, el sistema SHALL priorizarlo sobre el generado desde el logo.

#### Scenario: Prioridad del set dedicado
- **WHEN** un tenant tiene un icono de app dedicado además de su logo
- **THEN** las rutas de icono devuelven el asset dedicado sin cambiar las URLs del manifest ni del HTML
