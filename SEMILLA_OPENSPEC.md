# SEMILLA_OPENSPEC.md - Especificación Funcional por Módulos (Semilla OpenSpec)

Este documento define de forma modular y estructurada los requerimientos funcionales, flujos de estados, reglas de negocio y navegación del sistema **vendemostuautomovil.com**. Está diseñado para servir como semilla directa para herramientas de desarrollo guiado por especificaciones (OpenSpec/SSD).

---

## Módulo 0: Arquitectura Core SaaS (Multitenancy & RBAC)

### 0.1. Aislamiento Multitenant
* **Descripción:** El sistema opera bajo un modelo SaaS (Software as a Service) utilizando la estrategia de **Aislamiento por Fila (Shared Database, Discriminator Column)**.
* **Regla de Negocio:** Cada tabla del sistema (usuarios, vehículos, sucursales, contratos, auditoría, liquidaciones) debe poseer obligatoriamente una llave foránea `tenant_id`. Ninguna consulta (SELECT, UPDATE, DELETE) puede ejecutarse sin filtrar estrictamente por el `tenant_id` del contexto del usuario autenticado. Los datos de *vendemostuautomovil.com* jamás deben mezclarse con los de futuros clientes de la plataforma.

### 0.2. Control de Acceso Basado en Roles (RBAC)
* **Descripción:** Gestión estricta de permisos para usuarios internos y externos basada en roles predefinidos.
* **Matriz Operativa de Roles:**
    * `SuperAdmin (Platform Owner):` Acceso global a nivel de infraestructura multi-tenant.
    * `TenantAdmin (CEO / Bastian Galve):` Acceso total a los datos de su propia empresa y visualización del Estado de Resultados integral.
    * `Management (Josefa Cuevas):` Permisos de lectura/escritura transversales, control del checklist y aprobación obligatoria para pasar vehículos a estado `PUBLICADO`.
    * `Sales Team (Araneth Díaz / Cristian Farías):` Permisos restringidos a la gestión de prospección, emisión de actas de recepción en sucursales asignadas y agendamiento de visitas. No visualizan métricas globales del negocio.
    * `Client (Propietario del Auto):` Rol externo con acceso limitado exclusivamente a la visualización del estado de su propio vehículo y confirmación de términos comerciales.

---

## Módulo 1: Tasación e Inteligencia de Mercado (Prospección)

### 1.1. Descripción General
Permite capturar datos iniciales de un vehículo y estimar valores competitivos de venta utilizando algoritmos internos combinados con la extracción automatizada de datos del mercado automotriz chileno.

### 1.2. Reglas de Negocio
* **Entrada de Datos Requerida:** Patente (PPU) válida en Chile y Kilometraje actual.
* **Motor de Scraping:** El sistema debe consultar de forma asíncrona fuentes de mercado de referencia (como Chileautos) buscando coincidencias de marca, modelo, versión y año de fabricación.
* **Cálculo de Precios:** La API del backend debe procesar los datos extraídos y retornar tres umbrales de precio financieros:
    * *Precio Mercado:* Promedio directo de los vehículos publicados activos.
    * *Precio Retoma:* Valor ajustado a la baja para compra rápida.
    * *Precio Publicación Sugerido:* Valor óptimo estimado para la venta por corretaje.

### 1.3. Resultados Esperados
* Persistencia del prospecto en base de datos con estado inicial `PROSPECTO`, indexado con el `tenant_id` correspondiente.
* Agendamiento de inspección física en una sucursal habilitada de la corredora.

---

## Módulo 2: Inspección y Formalización (Consignación Virtual)

### 2.1. Descripción General
Módulo utilizado por los ejecutivos en sucursal (ej: Araneth Díaz) para recibir físicamente el vehículo, realizar el peritaje digital y formalizar el contrato legal de corretaje mientras el dueño conserva la posesión del auto.

### 2.2. Reglas de Negocio
* **Acta de Recepción Digital:** Formulario estricto en el Backoffice, fiel al documento real que firma el cliente. Recopila:
    1.  *Antecedentes del Cliente:* RUT, Nombre Completo, **Domicilio**, **Comuna** (catálogo), Teléfono (Fono) y Correo.
    2.  *Antecedentes del Vehículo:* **Tipo de Vehículo** (catálogo), Marca, Modelo, N° Motor, N° Chasis, **Combustible** (catálogo), **Color**, Año, Kilometraje y Patente (PPU).
    3.  *Checklist de Documentos y Accesorios (12 puntos reales):* cada fila se marca SÍ/NO, con Fecha de Recepción y Observaciones. Los tres primeros exigen fecha de vencimiento.
        1. Permiso de Circulación *(vence)* — 2. Seguro Obligatorio *(vence)* — 3. Revisión Técnica *(vence)* — 4. Copia de Llave — 5. Manual de Usuario — 6. Dispositivo TAG — 7. Rueda de Repuesto — 8. Gata — 9. Herramienta — 10. Kit de Seguridad — 11. Panel desmontable — 12. Pisos de goma.
    4.  *Observaciones generales* de la recepción.
* **Orden de Venta:** Definición de condiciones comerciales de corretaje:
    * *Tipo de Comisión:* catálogo `tipos_comision` con tasa y mínimo (Estándar 5% / Gold 3%, ambos con mínimo $440.000). Se elige al levantar el acta.
    * *Precio de Venta Pactado:* Monto al cual se ofrecerá el auto.
    * *Comisión (derivada):* `MAX(Precio × tasa, mínimo)`. No se persiste; se calcula en lectura.
    * *Liquidación de Pago (derivada):* `Precio − Comisión`. Monto que recibe el cliente.
    * *Vigencia:* Contrato base de 30 días corridos renovables.
    * *Cláusula de Exclusividad:* Abono de $40.000 al firmar. **Es un anticipo de comisión, no un depósito reembolsable:** al concretarse la venta se descuenta de la comisión pactada; si el auto se vende por fuera o el dueño desiste, la empresa lo retiene como ingreso por gestión.
* **Asignación de Comisiones de Captación:** El sistema debe registrar obligatoriamente al ejecutivo que levanta el acta (**ejecutivo captador**) y la **sucursal de origen** (ej: Araneth Díaz en Sucursal Rancagua).
* **Definición de la Sucursal de Venta (Derivación entre Sucursales):** Al levantar el acta, el ejecutivo captador debe indicar **obligatoriamente** quién gestionará la venta, eligiendo una de dos opciones:
    * *La venta la realizo yo:* La `sucursal_venta` se fija igual a la sucursal de origen. El propio captador queda habilitado como potencial vendedor.
    * *Derivar la venta a otra sucursal:* El captador selecciona la **sucursal de venta** de destino (ej: consigna en Rancagua un auto que debe venderse en Santiago). No se asigna un ejecutivo nominal: **cualquier ejecutivo de la sucursal de venta** queda habilitado para tomar y cerrar la venta.
    * **Regla de Negocio:** El sistema modela `sucursal_origen` (captación) y `sucursal_venta` como dos referencias independientes. Cuando difieren, el auto se considera **derivado** y solo es visible para la gestión de venta (agendamiento de visitas y cierre) por ejecutivos cuya sucursal asignada coincida con `sucursal_venta`.

### 2.3. Documento de Firma (PDF corporativo de 2 hojas)
El sistema genera un PDF imprimible, disponible desde el estado `CONTRATO_ACEPTADO`, que reproduce el documento real que firma el cliente. Ambas hojas comparten el **encabezado corporativo**: barra de marca con el **logo del tenant**, razón social, RUT de la empresa, giro, dirección de la sucursal de origen, teléfono, web, más el título, la **PPU** y la fecha en formato largo en español.

* **Hoja 1 — ACTA DE RECEPCIÓN DIGITAL:** Antecedentes del Cliente, Antecedentes del Vehículo, la tabla del checklist de 12 puntos (SÍ/NO, fecha de recepción, observaciones/vencimientos), bloque de Observaciones y **tres firmas**: *Recepción a cargo de* (ejecutivo), *Firma Cliente* y *Huella* (con RUT del cliente).
* **Hoja 2 — ORDEN DE VENTA:** Texto de autorización al mandatario, Antecedentes del Vehículo, **Condiciones del Contrato** (Tipo de Comisión, Precio, Comisión, Vigencia, Liquidación de Pago, Abono de exclusividad), las cláusulas legales **PRIMERO a SEXTO**, y **tres firmas**: *Firma Mandante* (cliente + RUT), *Firma Ejecutivo* (**RUT del ejecutivo**) y *Firma Mandatario* (empresa + RUT).

**Datos que esto exige del modelo:** el `tenant` almacena razón social, RUT, giro, teléfono, web y logo; el `user` (ejecutivo) almacena su **RUT** para la firma de la Orden de Venta.

### 2.4. Transición de Estados y Automatización (n8n)
* Al guardar el formulario, el estado del auto cambia a `RECEPCIONADO`.
* **Trigger n8n:** El cambio de estado gatilla un webhook que envía un correo automatizado al cliente con el resumen del contrato (Cargos de 2 UF de estacionamiento post día 31, coordinación exclusiva de visitas en oficina, penalizaciones por accesorios faltantes declarados, cobro de $7.490 + IVA por limpieza de multas, plazos de liquidación).
* El cliente debe responder con el texto exacto *"ACEPTO LOS TÉRMINOS Y CONDICIONES"*, lo cual habilita el paso a estado `CONTRATO_ACEPTADO`.

---

## Módulo 3: Validación y Publicación (Catálogo Automatizado)

### 3.1. Descripción General
Filtro administrativo y comercial encargado de verificar el expediente digital del auto antes de lanzarlo al mercado público.

### 3.2. Reglas de Negocio
* **Control de Operaciones:** El rol de **Management (Josefa Cuevas)** es el único perfil autorizado en el Backoffice para revisar el Acta de Recepción, verificar que las fotos profesionales estén cargadas correctamente y presionar el botón de activación.
* **Inyección Automatizada:** Al autorizar la ficha, el estado cambia a `PUBLICADO`. El Backend expone inmediatamente el vehículo en los endpoints consumidos por la Landing Page pública en Next.js, haciéndolo visible en el catálogo de cara a los compradores.

---

## Módulo 4: Gestión de Interacciones (Agendamiento de Visitas)

### 4.1. Descripción General
Herramienta de matchmaking encargada de conectar el interés de un comprador online con el propietario que mantiene el auto en modalidad virtual.

### 4.2. Reglas de Negocio
* **Origen:** El vendedor del Backoffice (ej: Cristian Farías) recibe el interés de un tercero y genera una solicitud de visita en la plataforma. Solo pueden gestionar visitas y cerrar la venta de un auto los ejecutivos cuya sucursal asignada coincida con la `sucursal_venta` definida en el Acta de Recepción. Si el auto fue **derivado**, cualquier ejecutivo de la sucursal de venta puede tomarlo (no está asignado nominalmente).
* **Coordinación Logística:** El software solicita fecha, hora y sucursal. Se prohíben de forma estricta los encuentros fuera de las dependencias oficiales de la empresa (Santiago o Rancagua).
* **Notificación y Confirmación:** n8n notifica al propietario para confirmar disponibilidad. Al aceptar, el auto entra transitoriamente en estado `PUBLICADO` con indicador de `CON VISITA PROGRAMADA`.
* **Preparación obligatoria del auto:** Al propietario se le instruye por correo que el auto debe presentarse limpio, aspirado y sin pertenencias personales.

---

## Módulo 5: Liquidación Comercial, Comisiones Cruzadas y Estado de Resultados

### 5.1. Descripción General
Procesamiento de la venta definitiva, cálculo dinámico de incentivos para los ejecutivos que participaron en el ciclo de vida del auto y consolidación analítica para la dirección ejecutiva.

### 5.2. Reglas de Negocio Financieras
* **Cálculo del Fee Corporativo (Comisión de Corretaje):** el tipo de comisión vive en el catálogo `tipos_comision` (tasa + mínimo), se elige en el acta y **no se hardcodea**:
    * *Comisión Estándar (5%):* `MAX(Precio_Venta * 0.05, 440000)`. Si el 5% es menor a $440.000, se cobra el valor mínimo estipulado.
    * *Comisión Gold (3%):* `MAX(Precio_Venta * 0.03, 440000)`. Exclusiva para clientes con 2 o más ventas por la plataforma, o autos high ticket (sobre MM$60).
    * *Liquidación de Pago:* `Precio_Venta − Comisión`. Es el monto que se transfiere al cliente.
    * *Comisión Preferencial (Fidelidad):* Si el RUT del dueño registra más de 3 ventas históricas completadas en el sistema del inquilino (`tenant_id`), se desbloquea automáticamente una tasa preferencial configurada por la administración.
    * *Abono de exclusividad ($40.000):* es **anticipo de comisión**, no un pasivo reembolsable. Al vender, el cliente paga `Comisión − Abono`; si no se concreta por su decisión, la empresa lo retiene como ingreso. Nunca se modela como devolución en efectivo.
* **Reparto de Comisión Cruzada:** Cuando el auto pasa a estado `VENDIDO`, el sistema liquida y distribuye las comisiones de los empleados según sus roles asignados:
    * *Monto Ejecutivo Captador:* Asociado a quien generó el Acta de Recepción (ej: Araneth Díaz en Rancagua). **Este monto se conserva íntegro aunque la venta haya sido derivada a otra sucursal:** el captador siempre cobra su parte por la captación, independientemente de dónde se cierre la venta.
    * *Monto Ejecutivo Vendedor:* Asociado a quien efectivamente coordinó la visita y cerró la venta (ej: Cristian Farías en Santiago), aunque pertenezca a una sucursal distinta a la de captación.
* **Plazos y Retenciones para Administración:**
    * *Venta Contado:* Liquidación al cliente final en 2 días hábiles tras la entrega.
    * *Venta Financiamiento:* Pie liquidado en 2 días hábiles; saldo financiado en un plazo máximo de 10 días hábiles.
    * *Retención por Prenda/Multas:* El sistema congela la orden de pago si se marca que el auto posee prendas pendientes, liberando los fondos solo cuando el nuevo padrón esté emitido a nombre del comprador.

### 5.3. Métricas del Estado de Resultados para el CEO (Bastian Galve)
El Backoffice debe calcular dinámicamente un dashboard financiero filtrado estrictamente por `tenant_id` para todos los autos consolidados como `VENDIDO`:
1.  **Ingresos Brutos:** Suma de Comisiones de Corretaje + Cobros por días extras de estacionamiento (2 UF mensuales a partir del día 31) + Cobros por limpieza de multas ($7.490 + IVA c/u) + Retenciones de exclusividad aplicadas.
2.  **Costos Directos:** Comisiones totales pagadas a los captadores + comisiones totales pagadas a los vendedores + costos asociados de consulta/scrapers.
3.  **Margen Neto:** Utilidad operacional real de la empresa disponible para filtros por fechas y sucursales.

---

## Módulo 6: Seguridad y Registro Inmutable (Auditoría)

### 6.1. Descripción General
Mecanismo de resguardo técnico para garantizar la transparencia absoluta de los datos ingresados.

### 6.2. Reglas de Negocio
* Cada evento o mutación de datos sobre un vehículo genera una inserción inalterable en la tabla `logs_auditoria`.
* Está estrictamente prohibido el uso de sentencias `UPDATE` o `DELETE` sobre dicha tabla (Estrategia de Append-Only).
* **Datos mandatorios por Log:** `tenant_id`, ID del usuario transaccional, marca de tiempo del servidor (Timestamp), IP, Estado Anterior, Estado Nuevo y JSON con el Payload detallando los campos modificados.

---

## Módulo 7: Estructura Dinámica de Menús en el Backoffice

### 7.1. Descripción General
La interfaz de usuario del Backoffice (React 18 + Vite + TS) renderiza las opciones de navegación lateral (Sidebar) basándose estrictamente en el rol del usuario autenticado (`role_id`) y su contexto SaaS (`tenant_id`), consumiendo el endpoint `GET /api/v1/navigation/menu`.

### 7.2. Opciones de Navegación por Rol

#### 1. Rol: Sales Team (Ejecutivos de Venta/Captación)
* **🚗 Gestión de Vehículos**
    * `Tasación Rápida`: Formulario de ingreso de Patente (PPU) y Kilometraje para simulación.
    * `Mis Captaciones`: Lista de autos ingresados por el ejecutivo filtrados por estados operativos.
    * `Nueva Acta de Recepción`: Formulario digital del peritaje de 12 puntos, carga de fotografías y definición de sucursal de venta (venta propia o derivación a otra sucursal).
    * `Ventas Derivadas a mi Sucursal`: Bandeja de autos captados en otra sede cuya `sucursal_venta` es la del ejecutivo; cualquier ejecutivo de la sucursal puede tomarlos para agendar visitas y cerrar la venta.
* **📅 Agenda de Visitas**
    * `Calendario de Muestras`: Agenda semanal de citas coordinadas en sucursal de origen.
    * `Crear Solicitud de Visita`: Registro de potenciales compradores interesados en un auto del catálogo.
* **💰 Mis Comisiones**
    * `Historial de Incentivos`: Panel personal de comisiones devengadas (captación/venta) y estados de pago.

#### 2. Rol: Management (Administración y Operaciones - Josefa Cuevas)
* **📋 Control y Validaciones**
    * `Pendientes de Aprobación`: Bandeja de autos en `CONTRATO_ACEPTADO` para verificación final.
    * `Gestor del Catálogo`: Panel maestro para habilitar, deshabilitar, o editar autos `PUBLICADO`.
* **🏢 Operaciones Sucursales**
    * `Monitoreo de Visitas`: Tablero global de todas las citas agendadas entre sucursales.
    * `Control de Custodia`: Tracking de permanencia física en sucursales y alertas automáticas post día 31.
* **🏦 Módulo de Liquidaciones**
    * `Órdenes de Pago`: Gestión de transferencias a clientes por plazos contractuales (2 o 10 días).
    * `Retenciones por Prenda/Multas`: Control de fondos congelados por incidencias de dominio o infracciones.

#### 3. Rol: TenantAdmin (CEO de la Automotora - Bastian Galve)
* **📊 Business Intelligence (BI)**
    * `Estado de Resultados`: Dashboard financiero en tiempo real (Ingresos Brutos, Costos Directos, Margen Neto).
    * `Performance de Equipo`: Reportes de efectividad, tasas de conversión y velocidad de stock por ejecutivo.
* **⚙️ Configuración del Negocio**
    * `Parámetros de Comisión`: Modificación de tasas corporativas (5%, 3% y cobros mínimos de $440.000).
    * `Reglas de Fidelidad`: Parametrización del umbral de volumen para clientes preferenciales (>3 autos).
    * `Gestión de Usuarios`: Control de personal y asignación de roles RBAC dentro de la empresa.

#### 4. Rol: SuperAdmin (Propietario Global del SaaS)
* **🌐 Panel de Inquilinos (Tenants)**
    * `Directorio de Clientes`: ABM (Alta/Baja/Modificación) de automotoras integradas al SaaS.
    * `Métricas de Consumo`: Estado de la infraestructura, volumen de base de datos y uso de APIs.
    * `Facturación SaaS`: Control de licencias y cobros recurrentes de la plataforma.