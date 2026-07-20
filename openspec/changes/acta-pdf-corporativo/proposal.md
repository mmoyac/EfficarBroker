## Why

El PDF de firma actual es un layout genérico que no coincide con el documento real que la empresa hace firmar al cliente. El acta real de *vendemostuautomovil.com* es un documento corporativo de **dos hojas** (Hoja 1: Acta de Recepción; Hoja 2: Orden de Venta) con encabezado de marca, datos de empresa, campos que hoy no capturamos (domicilio/comuna del cliente; tipo/combustible/color del vehículo; tipo de comisión), un checklist de 12 puntos distinto al seedeado, cláusulas legales y tres bloques de firma. Este cambio alinea el sistema y el PDF con ese documento real.

## What Changes

- **Nuevos campos de cliente:** `domicilio` (texto) y `comuna_id` (FK a catálogo `comunas`).
- **Nuevos campos de vehículo:** `tipo_vehiculo_id` (FK `tipos_vehiculo`), `combustible_id` (FK `combustibles`), `color` (texto) y `tipo_comision_id` (FK `tipos_comision`).
- **Nuevos catálogos** (regla dura del proyecto): `comunas`, `tipos_vehiculo`, `combustibles`, `tipos_comision` (con `tasa` y `minimo`).
- **Datos corporativos en `tenants`:** `razon_social`, `rut`, `giro`, `telefono`, `web`, `logo`. El encabezado del PDF usa el **logo del tenant** y estos datos; la dirección del encabezado sale de la sucursal de origen.
- **RUT en `users`:** campo `rut` (requerido para ejecutivos) — necesario para "Firma Ejecutivo" en la Orden de Venta.
- **Checklist real de 12 puntos:** reemplazar el catálogo `checklist_items` seedeado por los puntos del acta real (Permiso de Circulación, Seguro Obligatorio, Revisión Técnica, Copia de Llave, Manual de Usuario, Dispositivo TAG, Rueda de Repuesto, Gata, Herramienta, Kit de Seguridad, Panel desmontable, Pisos de goma).
- **Cálculos derivados de comisión:** `comision = MAX(precio_venta_pactado × tasa, minimo)` y `liquidacion = precio_venta_pactado − comision`, según el `tipo_comision` (Estándar 5% / Gold 3%, mínimo $440.000). No se persisten.
- **PDF de firma corporativo de 2 hojas:**
  - *Hoja 1 — Acta de Recepción:* encabezado (logo tenant + datos empresa), antecedentes del cliente (con domicilio/comuna), antecedentes del vehículo (tipo/combustible/color), checklist de 12 puntos con fecha de recepción y observaciones, observaciones generales, y firmas: Recepción a cargo de (ejecutivo), Firma Cliente, Huella.
  - *Hoja 2 — Orden de Venta:* encabezado, texto de autorización, antecedentes del vehículo, condiciones del contrato (tipo de comisión, precio, comisión, vigencia, liquidación de pago), 6 cláusulas legales (PRIMERO–SEXTO) y firmas: Mandante (cliente), Ejecutivo, Mandatario (empresa) con sello.
- **Formulario y API del acta:** `ActaCreate` acepta los campos nuevos; endpoints de catálogo para comunas, tipos de vehículo, combustibles y tipos de comisión; seed de catálogos, datos corporativos del tenant y RUT de ejecutivos.

## Capabilities

### New Capabilities
- `acta-pdf-corporativo`: Documento de firma corporativo de dos hojas (Acta de Recepción + Orden de Venta) fiel al formato real, incluyendo los campos, catálogos y datos de empresa que lo alimentan.

### Modified Capabilities
<!-- Las specs de acta-recepcion no están archivadas en openspec/specs/; por convención del
     proyecto la nueva plantilla y campos se consolidan en la capacidad nueva acta-pdf-corporativo,
     que reemplaza el documento genérico anterior. -->

## Impact

- **Base de datos (migración 0009):** columnas nuevas en `clientes` (domicilio, comuna_id), `vehiculos` (tipo_vehiculo_id, combustible_id, color, tipo_comision_id), `users` (rut), `tenants` (razon_social, rut, giro, telefono, web, logo); tablas catálogo `comunas`, `tipos_vehiculo`, `combustibles`, `tipos_comision`.
- **Seed:** reemplazo de los 12 `checklist_items`; catálogos nuevos; datos corporativos del tenant vendemostuautomovil; RUT de los ejecutivos; comuna de los clientes demo.
- **APIs:** `ActaCreate` y serializers amplían campos; nuevos `GET /comunas`, `/tipos-vehiculo`, `/combustibles`, `/tipos-comision`; `GET /vehiculos/{id}/documento-firma` genera el PDF de 2 hojas.
- **Backoffice:** el formulario `/actas/nueva` suma domicilio/comuna, tipo/combustible/color y tipo de comisión (con vista previa de comisión y liquidación).
- **Diferido:** UI de "Parámetros de Comisión" para editar tasas/mínimos (M5); logo/sello propios adicionales al del tenant; lista completa de comunas de Chile (se seedea un subconjunto inicial).
- **Dependencia:** convive con el cambio `derivacion-venta-sucursal` (sucursal de venta); ambos tocan `vehiculos` — las migraciones se ordenan por `down_revision`.
