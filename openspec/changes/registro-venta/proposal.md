## Why

El negocio tiene dos comisiones distintas: la del **captador** (quien levanta el acta) y la del **vendedor** (quien cierra la venta). Hoy la recepción ya registra al captador, pero no existe forma de asignar al vendedor ni de registrar la venta. Este cambio cierra el ciclo mínimo para el ejemplo Araneth (capta) → Cristian (vende), dejando el auto en `VENDIDO` con ambos ejecutivos registrados y con las fechas para KPIs.

## What Changes

- **Campos de venta en el vehículo:** `vendedor_user_id` (nullable), `precio_venta_final` (nullable), `fecha_venta` (nullable).
- **Registrar venta:** `POST /api/v1/vehiculos/{id}/registrar-venta` (Sales/Management/TenantAdmin) que recibe `vendedor_user_id` y `precio_venta_final`, valida que el vendedor sea un usuario de ventas activo del tenant, transita el auto a `VENDIDO`, registra historial de estado y auditoría. Versión simplificada: permitido desde `CONTRATO_ACEPTADO` o `PUBLICADO` (no exige pasar por publicación).
- **Equipo de ventas:** `GET /api/v1/equipo-ventas` — usuarios `Sales` activos del tenant, para elegir vendedor (accesible a los roles que operan actas).
- **Corrección:** `GET /api/v1/sucursales` ahora es accesible a `Sales` (antes solo `TenantAdmin`), para que el ejecutivo pueda seleccionar la sucursal de recepción.
- **Backoffice:** en "Mis Captaciones", acción "Registrar venta" (selecciona vendedor + precio final) y columnas de captador/vendedor; muestra el estado `VENDIDO`.

## Capabilities

### New Capabilities
- `registro-venta`: Asignación del vendedor y registro de la venta del vehículo (→ `VENDIDO`), capturando precio final y fecha, base para las comisiones cruzadas.

### Modified Capabilities
<!-- Ninguna delta sobre specs archivadas: capacidad nueva. -->

## Impact

- **Base de datos:** columnas `vendedor_user_id`, `precio_venta_final`, `fecha_venta` en `vehiculos` (migración 0005).
- **APIs nuevas:** `POST /vehiculos/{id}/registrar-venta`, `GET /equipo-ventas`; ajuste de guard en `GET /sucursales`.
- **Backend:** transición a `VENDIDO` con historial + auditoría; registro de captador y vendedor.
- **Backoffice:** acción de registrar venta en captaciones.
- **Base para M5:** con captador + vendedor + precio final + fechas, el cálculo de comisiones cruzadas y el Estado de Resultados quedan habilitados.
