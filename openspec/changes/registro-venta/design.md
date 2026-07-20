## Context

Extensión mínima del Módulo 2 hacia el Módulo 5: capturar al vendedor y registrar la venta para habilitar las dos comisiones (captación y venta). Se decidió versión simplificada (sin exigir `PUBLICADO`) y precio final ingresado al registrar la venta.

## Goals / Non-Goals

**Goals:**
- Registrar la venta de un vehículo, asignando vendedor y precio final, dejándolo en `VENDIDO`.
- Mantener captador (recepción) y vendedor (venta) como usuarios distintos, base de las comisiones cruzadas.
- Capturar `fecha_venta` e historial de estado para KPIs.

**Non-Goals:**
- Cálculo/liquidación de comisiones y Estado de Resultados (M5 completo).
- Flujo de publicación (M3) y visitas (M4) como prerequisito.
- Financiamiento, retenciones por prenda/multas.

## Decisions

### D1 — Campos de venta en `vehiculos`
Se agregan `vendedor_user_id` (FK users, nullable), `precio_venta_final` (int, nullable), `fecha_venta` (date, nullable). Nullable porque solo se llenan al vender.

### D2 — Transición simplificada a VENDIDO
`registrar-venta` se permite si el estado actual es `CONTRATO_ACEPTADO` o `PUBLICADO` (no exige publicación). Rechaza si ya está `VENDIDO` o si aún está en `RECEPCIONADO`/`PROSPECTO` (debe existir contrato aceptado). Registra historial + auditoría.

### D3 — Vendedor válido
El `vendedor_user_id` debe ser un usuario **activo** del tenant con rol `Sales`. El captador y el vendedor pueden ser la misma persona o distintos (en el ejemplo, distintos). `GET /equipo-ventas` provee la lista para el selector.

### D4 — Precio final independiente del pactado
`precio_venta_final` puede diferir del `precio_venta_pactado`. Las comisiones (M5) se calcularán sobre el precio final.

## Risks / Trade-offs

- **Saltarse PUBLICADO/visitas** simplifica pero no refleja el flujo real → aceptable para demo; el flujo completo llega en M3/M4. La máquina de estados formal se centralizará luego.
- **Sin validación de que el vendedor participó en una visita** → en esta etapa cualquier Sales activo puede asignarse; se refinará con M4.

## Open Questions

- ¿El vendedor debe poder ser también Management/TenantAdmin? — Por ahora solo `Sales`; ampliable si el negocio lo pide.
