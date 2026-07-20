## ADDED Requirements

### Requirement: Catálogos de comuna, tipo de vehículo, combustible y tipo de comisión
El sistema SHALL modelar como tablas catálogo `comunas`, `tipos_vehiculo`, `combustibles` y `tipos_comision`, y exponerlas vía `GET /api/v1/comunas`, `GET /api/v1/tipos-vehiculo`, `GET /api/v1/combustibles` y `GET /api/v1/tipos-comision`. `tipos_comision` SHALL incluir `code`, `nombre`, `tasa` (fracción) y `minimo` (CLP).

#### Scenario: Obtener tipos de comisión
- **WHEN** un usuario autorizado consulta `GET /api/v1/tipos-comision`
- **THEN** recibe al menos Estándar (tasa 0.05, mínimo 440000) y Gold (tasa 0.03, mínimo 440000)

#### Scenario: Combustible y tipo de vehículo disponibles para el formulario
- **WHEN** el ejecutivo abre el formulario de acta
- **THEN** puede seleccionar tipo de vehículo y combustible desde sus catálogos

### Requirement: Datos corporativos del tenant para el documento
El sistema SHALL almacenar en `tenants` los datos corporativos usados en el encabezado y firma del documento: `razon_social`, `rut`, `giro`, `telefono`, `web` y `logo`. El encabezado del PDF SHALL usar el logo del tenant; la dirección del encabezado SHALL provenir de la sucursal de origen del vehículo.

#### Scenario: Encabezado con datos del tenant
- **WHEN** se genera el documento de firma
- **THEN** el encabezado muestra el logo del tenant, su razón social, RUT, giro, teléfono y web

#### Scenario: Tenant sin logo cargado
- **WHEN** el tenant no tiene logo definido
- **THEN** el documento se genera igualmente, reservando el espacio del logo sin romper el layout

### Requirement: Campos ampliados de cliente y vehículo en el acta
El sistema SHALL capturar y persistir, al levantar el acta, `domicilio` y `comuna_id` del cliente, y `tipo_vehiculo_id`, `combustible_id`, `color` y `tipo_comision_id` del vehículo. Los campos de catálogo SHALL validar que la referencia exista; `tipo_comision_id` SHALL ser obligatorio.

#### Scenario: Alta de acta con campos ampliados
- **WHEN** un ejecutivo envía un acta con domicilio, comuna, tipo de vehículo, combustible, color y tipo de comisión válidos
- **THEN** el vehículo y el cliente se crean con esos datos persistidos

#### Scenario: Referencia de catálogo inválida
- **WHEN** se envía un `comuna_id`, `tipo_vehiculo_id`, `combustible_id` o `tipo_comision_id` inexistente
- **THEN** el sistema responde `400`

### Requirement: RUT del ejecutivo
El sistema SHALL almacenar `rut` en `users` y usarlo en el bloque "Firma Ejecutivo" de la Orden de Venta. El RUT del ejecutivo SHALL estar presente para los usuarios que levantan actas.

#### Scenario: Firma ejecutivo con RUT
- **WHEN** se genera la Orden de Venta
- **THEN** el bloque de firma del ejecutivo muestra su RUT

### Requirement: Cálculo de comisión y liquidación
El sistema SHALL calcular la comisión como `MAX(precio_venta_pactado × tasa, minimo)` según el `tipo_comision` del vehículo, y la liquidación de pago como `precio_venta_pactado − comision`. Estos valores SHALL derivarse en tiempo de lectura y NO persistirse.

#### Scenario: Comisión estándar con mínimo aplicado
- **WHEN** el precio pactado es $7.690.000 con tipo de comisión Estándar (5%, mínimo $440.000)
- **THEN** la comisión calculada es $440.000 (porque 5% = $384.500 < mínimo) y la liquidación es $7.250.000

#### Scenario: Comisión por porcentaje
- **WHEN** el precio pactado es $12.000.000 con tipo Estándar (5%, mínimo $440.000)
- **THEN** la comisión calculada es $600.000 y la liquidación es $11.400.000

### Requirement: Checklist de 12 puntos del acta real
El sistema SHALL seedear el catálogo `checklist_items` con los 12 puntos del acta real: Permiso de Circulación, Seguro Obligatorio, Revisión Técnica (los tres con vencimiento), Copia de Llave, Manual de Usuario, Dispositivo TAG, Rueda de Repuesto, Gata, Herramienta, Kit de Seguridad, Panel desmontable y Pisos de goma.

#### Scenario: Checklist coincide con el acta real
- **WHEN** se consulta `GET /api/v1/checklist-items`
- **THEN** se obtienen exactamente esos 12 puntos, con indicador de vencimiento en los tres documentos legales

### Requirement: PDF de firma corporativo de dos hojas
El sistema SHALL generar en `GET /api/v1/vehiculos/{id}/documento-firma` un PDF de dos hojas fiel al formato real. La Hoja 1 SHALL ser el Acta de Recepción y la Hoja 2 la Orden de Venta, cada una con el encabezado corporativo (logo del tenant + datos de empresa), la PPU y la fecha.

#### Scenario: Contenido de la Hoja 1 (Acta de Recepción)
- **WHEN** se genera el documento
- **THEN** la Hoja 1 incluye: antecedentes del cliente (RUT, nombre, domicilio, comuna, fono, email), antecedentes del vehículo (tipo, marca, modelo, n° motor, n° chasis, combustible, color, año, kilometraje, patente), el checklist de 12 puntos con SI/NO, fecha de recepción y observaciones, un bloque de observaciones generales, y firmas: "Recepción a cargo de" (ejecutivo), "Firma Cliente" y "Huella"

#### Scenario: Contenido de la Hoja 2 (Orden de Venta)
- **WHEN** se genera el documento
- **THEN** la Hoja 2 incluye: texto de autorización al mandatario, antecedentes del vehículo, condiciones del contrato (tipo de comisión, precio, comisión, vigencia, liquidación de pago), las cláusulas PRIMERO a SEXTO, y firmas: "Firma Mandante" (cliente con RUT), "Firma Ejecutivo" (con RUT) y "Firma Mandatario" (empresa con RUT y sello)

#### Scenario: Disponibilidad por estado
- **WHEN** se solicita el documento para un vehículo en `RECEPCIONADO` o `PROSPECTO`
- **THEN** el sistema responde `409` (disponible desde `CONTRATO_ACEPTADO`, como hoy)

### Requirement: Backoffice — campos ampliados en el formulario de acta
El backoffice SHALL ampliar `/actas/nueva` para capturar domicilio y comuna del cliente, tipo de vehículo, combustible, color y tipo de comisión del vehículo, mostrando una vista previa de la comisión y la liquidación calculadas.

#### Scenario: Vista previa de comisión
- **WHEN** el ejecutivo ingresa el precio pactado y elige el tipo de comisión
- **THEN** la UI muestra la comisión y la liquidación de pago calculadas antes de guardar
