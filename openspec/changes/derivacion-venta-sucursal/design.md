## Context

`vehiculos` hoy tiene un único `sucursal_id` (la sede donde se recibe el auto) y `captador_user_id`/`vendedor_user_id`. El registro de venta (`POST /vehiculos/{id}/registrar-venta`) valida que el vendedor sea `Sales` activo del tenant, pero no considera la sucursal. La operación real usa dos sedes (Santiago, Rancagua) y necesita que un auto captado en una sede pueda venderse en la otra, con la venta abierta a cualquier ejecutivo de la sede destino (sin asignación nominal). Restricciones duras del proyecto: multitenancy por `tenant_id` en toda query, enums en catálogo, auditoría append-only, Pydantic strict.

## Goals / Non-Goals

**Goals:**
- Registrar la sucursal de venta por vehículo, distinta o no de la de origen.
- Decidir la derivación en el momento del acta, sin asignar ejecutivo nominal.
- Restringir la gestión de venta de autos derivados a ejecutivos de la sucursal de venta.
- Validar que el vendedor pertenezca a la sucursal de venta al registrar la venta.
- Backfill no destructivo de los vehículos existentes.

**Non-Goals:**
- Cálculo de comisiones cruzadas y Estado de Resultados (M5): solo se deja la regla especificada.
- Restricción de agendamiento de visitas por sucursal de venta (M4): se especifica pero su UI llega con M4.
- Re-derivar/cambiar la sucursal de venta después de creada el acta más allá de la edición ya existente en `RECEPCIONADO` (se permite vía el PATCH actual, ver Decisiones).

## Decisions

### 1. Columna nueva `sucursal_venta_id`, no renombrar `sucursal_id`
`sucursal_id` se mantiene como **sucursal de origen/captación** y se agrega `sucursal_venta_id` (NOT NULL, FK `sucursales`). Alternativa descartada: renombrar `sucursal_id → sucursal_origen_id` — rompería migraciones 0003/0005, el router, schemas y el PDF sin beneficio funcional. Se documenta la semántica en el modelo.

### 2. `derivado` es derivado, no persistido
`derivado = (sucursal_venta_id != sucursal_id)` se calcula en el serializer. Evita un flag redundante que podría desincronizarse. La bandeja de derivadas filtra por `sucursal_venta_id == user.sucursal_id AND sucursal_id != sucursal_venta_id`.

### 3. Migración con backfill en dos pasos
Agregar la columna como nullable → `UPDATE vehiculos SET sucursal_venta_id = sucursal_id` → alterar a NOT NULL + FK + índice. Idempotente respecto al seed (que también setea el valor). Migración 0008, `down_revision = 0007_vehiculo_catalogos`.

### 4. Validación de sucursal del vendedor en el endpoint existente
Se extiende `registrar_venta`: además de `Sales` activo del tenant, `vendedor.sucursal_id == vehiculo.sucursal_venta_id`. Los roles transversales que registran venta a nombre de un vendedor siguen pasando por esta validación (la restricción es sobre el vendedor, no sobre quién opera). Alternativa descartada: permitir override por `Management` — se deja fuera por ahora; si surge la necesidad se agrega como regla explícita.

### 5. Visibilidad vía parámetro `?derivadas=true` en el listado existente
Se reutiliza `GET /vehiculos` con un filtro nuevo en vez de crear un endpoint separado, consistente con el `?mine=true` ya existente. Para `Sales` filtra por su sucursal de venta; para roles transversales no restringe por sucursal.

## Risks / Trade-offs

- **[Backfill sobre datos productivos]** → El `UPDATE` de backfill es determinista (copia `sucursal_id`); se corre dentro de la migración antes de imponer NOT NULL, evitando filas huérfanas.
- **[Vendedor sin sucursal asignada]** → Usuarios `Sales` con `sucursal_id NULL` no pasarían la validación. Mitigación: el seed asigna sucursal a todos los `Sales`; la validación devuelve `400` con mensaje claro.
- **[Edición de la sucursal de venta post-acta]** → El PATCH actual solo edita `sucursal_id`; se extiende para permitir `sucursal_venta_id` mientras el auto esté en `RECEPCIONADO`, evitando estados inconsistentes tras la venta.
- **[Doble semántica de `sucursal_id`]** → Riesgo de confusión al leer código. Mitigación: docstring/comentarios en el modelo y nombres explícitos en los serializers (`sucursal_origen`, `sucursal_venta`).

## Migration Plan

1. Migración 0008: add `sucursal_venta_id` nullable → backfill `= sucursal_id` → set NOT NULL + FK `ondelete=RESTRICT` + índice.
2. Deploy backend con modelo/serializers/validación nuevos.
3. Seed actualizado (caso derivado Rancagua→Santiago) — idempotente.
4. Backoffice con toggle en el acta y bandeja de derivadas.
5. Rollback: `downgrade` elimina índice/FK/columna; el backend anterior ignora la columna.
