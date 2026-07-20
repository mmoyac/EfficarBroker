## 1. Backend — catálogos nuevos

- [x] 1.1 Modelar catálogo `comunas` (code/nombre; opcional región)
- [x] 1.2 Modelar catálogo `tipos_vehiculo` (code, nombre)
- [x] 1.3 Modelar catálogo `combustibles` (code, nombre)
- [x] 1.4 Modelar catálogo `tipos_comision` (code, nombre, tasa, minimo)
- [x] 1.5 Endpoints `GET /comunas`, `/tipos-vehiculo`, `/combustibles`, `/tipos-comision` (autenticados)

## 2. Backend — columnas nuevas

- [x] 2.1 `clientes`: + `domicilio` (texto), + `comuna_id` (FK `comunas`, nullable/backfill)
- [x] 2.2 `vehiculos`: + `tipo_vehiculo_id`, + `combustible_id` (FK), + `color` (texto), + `tipo_comision_id` (FK, requerido en alta)
- [x] 2.3 `users`: + `rut` (texto, nullable a nivel esquema)
- [x] 2.4 `tenants`: + `razon_social`, `rut`, `giro`, `telefono`, `web`, `logo`
- [x] 2.5 Migración Alembic 0009 con catálogos + columnas; resolver `down_revision` (encadenar tras 0008 si `derivacion-venta-sucursal` ya aplicado) para no crear dos cabezas

## 3. Backend — acta y cálculo de comisión

- [x] 3.1 `ActaCreate` + `ClienteIn`: agregar domicilio, comuna_id, tipo_vehiculo_id, combustible_id, color, tipo_comision_id; validar referencias de catálogo (400 si inválidas)
- [x] 3.2 `crear_acta`/`editar_vehiculo_recepcionado`: persistir los campos nuevos
- [x] 3.3 Helper `calcular_comision(precio, tipo_comision)` = `MAX(precio×tasa, minimo)`; `liquidacion = precio − comision`
- [x] 3.4 Serializers: exponer comuna, tipo_vehiculo, combustible, color, tipo_comision, comision y liquidacion (derivados)

## 4. Backend — seed

- [x] 4.1 Reemplazar `CHECKLIST_ITEMS` por los 12 puntos reales (Permiso Circulación, Seguro Obligatorio, Revisión Técnica con vencimiento; Copia de Llave, Manual de Usuario, Dispositivo TAG, Rueda de Repuesto, Gata, Herramienta, Kit de Seguridad, Panel desmontable, Pisos de goma)
- [x] 4.2 Seed catálogos: `tipos_comision` (Estándar 0.05/$440.000, Gold 0.03/$440.000), `combustibles`, `tipos_vehiculo`, `comunas` (subconjunto: comunas de clientes/sucursales demo)
- [x] 4.3 Seed datos corporativos del tenant vendemostuautomovil (razón social, RUT 77.141.304-8, giro, teléfono, web, logo)
- [x] 4.4 Seed `rut` de los ejecutivos; `domicilio`/`comuna` de clientes demo

## 5. Backend — PDF de dos hojas

- [x] 5.1 Helper `_header(canvas, tenant, sucursal, titulo, ppu, fecha)`: barra de marca + logo del tenant + datos de empresa + título + PPU + fecha larga en español
- [x] 5.2 `_acta_page`: antecedentes cliente (con domicilio/comuna), antecedentes vehículo (tipo/combustible/color), checklist 12 puntos (SI/NO + fecha recepción + observaciones), observaciones generales, firmas (Recepción/Cliente/Huella)
- [x] 5.3 `_orden_page`: autorización, antecedentes vehículo, condiciones (tipo comisión, precio, comisión, vigencia, liquidación), cláusulas PRIMERO–SEXTO, firmas (Mandante/Ejecutivo/Mandatario + sello)
- [x] 5.4 Ensamblar en `documento-firma`: hoja 1 acta + `showPage()` + hoja 2 orden; mantener guard de estado (≥ CONTRATO_ACEPTADO)

## 6. Backoffice

- [x] 6.1 Servicios/tipos de los nuevos catálogos y campos
- [x] 6.2 `/actas/nueva`: campos domicilio + comuna (cliente); tipo de vehículo, combustible, color, tipo de comisión (vehículo)
- [x] 6.3 Vista previa de comisión y liquidación al ingresar precio + tipo de comisión
- [x] 6.4 Reflejar los campos nuevos en el detalle del vehículo

## 7. Verificación

- [x] 7.1 `GET /checklist-items` devuelve los 12 puntos reales; catálogos nuevos responden
- [x] 7.2 Alta de acta con todos los campos nuevos; referencias de catálogo inválidas → 400
- [x] 7.3 Cálculo de comisión: precio $7.690.000 Estándar → comisión $440.000, liquidación $7.250.000; precio $12.000.000 → comisión $600.000
- [x] 7.4 `documento-firma` genera PDF de 2 hojas con encabezado (logo tenant), acta en hoja 1 y orden en hoja 2; firmas con RUT de cliente/ejecutivo/empresa
- [ ] 7.5 Validación visual con negocio contra el acta real (ajuste de layout)
