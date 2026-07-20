## Context

El PDF actual (`_build_acta_orden_pdf` en [vehiculos.py](../../../backend/src/routers/vehiculos.py)) es un layout genérico de una sola secuencia. El documento real es corporativo, de dos hojas (Acta + Orden de Venta), y exige datos que hoy no existen: domicilio/comuna del cliente, tipo/combustible/color del vehículo, tipo de comisión, RUT del ejecutivo y datos de empresa del tenant. Además el checklist seedeado no coincide con los 12 puntos reales. Restricciones duras: multitenancy por `tenant_id`, todo enum en catálogo, Pydantic strict, montos enteros CLP. Este cambio convive con `derivacion-venta-sucursal` (ambos tocan `vehiculos`).

## Goals / Non-Goals

**Goals:**
- Modelar los campos y catálogos que el documento real necesita.
- Reemplazar el checklist por los 12 puntos reales.
- Generar el PDF de dos hojas fiel al formato, usando el logo del tenant.
- Calcular comisión y liquidación como derivados.

**Non-Goals:**
- UI de edición de parámetros de comisión (tasas/mínimos) — se difiere a M5.
- Lista completa de comunas de Chile — se seedea un subconjunto inicial.
- Sello/logo adicionales al del tenant — por ahora solo el logo del tenant.

## Decisions

### 1. Catálogos nuevos con la regla dura del proyecto
`comunas`, `tipos_vehiculo`, `combustibles` y `tipos_comision` como tablas catálogo referenciadas por FK. `tipos_comision` lleva `tasa` (Numeric/fracción) y `minimo` (Integer CLP). Alternativa descartada: guardar tipo de comisión/combustible como texto libre — viola la convención de catálogos y complica el cálculo.

### 2. Comisión y liquidación derivadas, no persistidas
Se calculan en un helper a partir de `precio_venta_pactado` y del `tipo_comision` (`MAX(precio×tasa, minimo)`; liquidación = precio − comisión). Evita desincronización si cambia el precio pactado en `RECEPCIONADO`. La tasa/mínimo viven en el catálogo, no en el código.

### 3. Datos de empresa en `tenants`; dirección desde la sucursal
`razon_social`, `rut`, `giro`, `telefono`, `web`, `logo` en `tenants`. La dirección del encabezado sale de `vehiculo.sucursal` (origen), que ya tiene `direccion`. `logo` se almacena como referencia (path/URL o base64) y se embebe en el PDF; si falta, se reserva el espacio sin romper el layout.

### 4. RUT en `users` (no tabla aparte)
`users.rut` como columna simple (nullable a nivel de esquema para no romper al SuperAdmin de plataforma; requerido para ejecutivos vía seed/validación de negocio). Se usa solo para la firma del ejecutivo.

### 5. Reemplazo del checklist seedeado
El seed pasa a los 12 puntos reales (idempotente por `code`). En dev se parte de base limpia; los ítems antiguos que ya no aplican (extintor, llave de ruedas, triángulos, chaleco, padrón) no se re-siembran. No hay datos productivos que migrar.

### 6. Generación del PDF: dos `showPage()` explícitos
Se reestructura el generador en dos funciones (`_acta_page`, `_orden_page`) que comparten un helper de encabezado corporativo (`_header`). Se mantiene reportlab (ya en uso), sin dependencias nuevas. El encabezado dibuja la barra de marca + logo del tenant + bloque de datos de empresa + título + PPU + fecha en español.

### 7. Migración 0009 encadenada
`down_revision` apunta a la última migración vigente en el momento de aplicar (0007 o 0008 si `derivacion-venta-sucursal` ya se aplicó). Se resuelve el orden real al implementar para evitar dos cabezas de Alembic.

## Risks / Trade-offs

- **[Dos cambios tocan `vehiculos`]** → Coordinar `down_revision` de 0009 con la migración de `derivacion-venta-sucursal` (0008) para no crear ramas paralelas de Alembic.
- **[`comuna_id`/`combustible_id` obligatorios rompen actas existentes]** → Se agregan nullable o con backfill a un valor por defecto del catálogo; solo `tipo_comision_id` se exige en el alta nueva.
- **[Logo pesado embebido en cada PDF]** → Usar imagen optimizada; si el logo es grande, cachear/redimensionar. Mitigación simple: PNG pequeño del tenant.
- **[Fidelidad tipográfica]** → reportlab con Helvetica no replica exactamente la fuente de marca; se prioriza estructura/[jerarquía correcta sobre pixel-perfect. Ajuste fino en tarea de verificación con negocio.
- **[Subconjunto de comunas]** → Si el cliente ingresa una comuna no seedeada, falta la opción. Mitigación: seedear las comunas de los clientes/sucursales demo y permitir ampliar el catálogo después.

## Migration Plan

1. Migración 0009: catálogos nuevos + columnas en clientes/vehiculos/users/tenants (con backfill/nullable donde aplique).
2. Seed: 12 checklist reales, catálogos (tipos_comision Estándar/Gold, combustibles, tipos_vehiculo, comunas iniciales), datos corporativos del tenant, RUT de ejecutivos, comuna de clientes demo.
3. Backend: schemas/serializers ampliados + helper de comisión + generador PDF de 2 hojas.
4. Backoffice: campos nuevos en el formulario + vista previa de comisión.
5. Rollback: `downgrade` elimina columnas y catálogos; el generador anterior queda como referencia en git.
