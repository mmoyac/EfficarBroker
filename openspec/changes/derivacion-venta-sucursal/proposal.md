## Why

La empresa opera en dos sedes (Santiago y Rancagua) y es habitual que un ejecutivo consigne en su sucursal un auto que debe venderse en la otra (ej: Rancagua recibe un auto cuyo dueño y mercado están en Santiago). Hoy el acta solo registra la sucursal de origen y asume que la venta ocurre ahí mismo: no hay forma de derivar la venta a otra sucursal ni de restringir quién puede cerrarla. Esto rompe el flujo real de captación cruzada descrito en SEMILLA_OPENSPEC (Módulos 2, 4 y 5).

## What Changes

- **Sucursal de venta en el vehículo:** nueva columna `sucursal_venta_id` en `vehiculos` (FK a `sucursales`), independiente de `sucursal_id` (que pasa a leerse como **sucursal de origen/captación**). Backfill de filas existentes: `sucursal_venta_id = sucursal_id`.
- **Decisión de derivación en el acta:** al levantar el acta el captador indica obligatoriamente la sucursal de venta. Dos caminos:
  - *La venta la realizo yo:* `sucursal_venta_id = sucursal_id` (misma sede).
  - *Derivar la venta:* elige una sucursal de venta distinta del tenant. **No** se asigna ejecutivo nominal; cualquier ejecutivo de esa sucursal puede tomarla.
- **Regla derivada:** `derivado = (sucursal_venta_id != sucursal_id)`.
- **Visibilidad para gestión de venta:** los autos derivados solo son gestionables para venta (registrar venta / futuras visitas) por ejecutivos `Sales` cuya sucursal asignada coincida con `sucursal_venta_id`. `Management`/`TenantAdmin`/`SuperAdmin` mantienen visibilidad transversal.
- **Bandeja "Ventas Derivadas a mi Sucursal":** nuevo endpoint y opción de menú (`Sales`) que lista los autos vendibles cuya `sucursal_venta_id` es la sucursal del ejecutivo y su `sucursal_id` (origen) es otra.
- **Validación de venta por sucursal:** `POST /vehiculos/{id}/registrar-venta` SHALL rechazar un vendedor cuya sucursal no coincida con la `sucursal_venta_id` del vehículo (además de las validaciones actuales: Sales activo del tenant).
- **Comisión del captador intacta:** el captador conserva su comisión aunque la venta se derive; el vendedor efectivo puede ser de otra sucursal. (Sin cambios de código en M5 —aún no construido—; se deja documentado en la spec como regla financiera.)
- **Seed:** un caso derivado de ejemplo (auto captado en Rancagua con sucursal de venta Santiago) para validar el flujo end to end.

## Capabilities

### New Capabilities
- `derivacion-venta`: Definición de la sucursal de venta en el acta (venta propia o derivación a otra sucursal sin ejecutivo nominal), filtro de visibilidad de autos derivados por sucursal de venta, y validación de que el vendedor pertenezca a esa sucursal.

### Modified Capabilities
<!-- Las specs de acta-recepcion y registro-venta aún no están archivadas en openspec/specs/;
     por convención del proyecto, las nuevas reglas se consolidan en la capacidad nueva
     derivacion-venta, que extiende el comportamiento de ambas. -->

## Impact

- **Base de datos:** columna `sucursal_venta_id` (NOT NULL, FK `sucursales`) en `vehiculos` con backfill = `sucursal_id` (migración 0008).
- **APIs:** `POST /vehiculos` (acta) acepta `sucursal_venta_id`; `GET /vehiculos` gana filtro `?derivadas=true`; `POST /vehiculos/{id}/registrar-venta` valida sucursal del vendedor; `VehiculoOut`/`VehiculoDetailOut` exponen `sucursal_venta` y `derivado`.
- **Backend:** lógica de visibilidad por sucursal de venta reutilizando el scoping por tenant efectivo.
- **Backoffice:** selector de sucursal de venta en `/actas/nueva` (con toggle "la vendo yo / derivar") y página `/captaciones/derivadas`.
- **Seed:** caso derivado Rancagua→Santiago.
- **Diferido:** cálculo de comisiones cruzadas y Estado de Resultados (M5); agendamiento de visitas restringido por sucursal de venta (M4) queda especificado pero su UI se implementa con M4.
