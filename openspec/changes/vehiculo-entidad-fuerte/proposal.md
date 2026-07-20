## Why

Hoy la tabla `vehiculos` confunde cuatro conceptos en una sola fila: el auto (identidad física), su dueño, el acta de corretaje y la venta. Sumado al `UniqueConstraint("tenant_id","ppu")`, esto hace **imposible recepcionar dos veces el mismo vehículo**: el segundo ingreso es rechazado con 409, y forzarlo pisaría el `cliente_id` y los datos de la venta anterior, destruyendo el historial que alimenta los KPIs. Un auto es un bien durable que cambia de dueño varias veces; el sistema debe poder corretearlo tantas veces como vuelva.

En paralelo, el abono de exclusividad ($40.000) se guarda como un entero suelto, sin ciclo de vida. La empresa no puede distinguir la plata que ya ganó por gestión de la que todavía es un anticipo no devengado, ni responder cuánto tiene comprometido en abonos vigentes.

## What Changes

- **BREAKING — Separación de entidades:** `vehiculos` pasa a ser entidad fuerte con la sola identidad física del auto (PPU, marca, modelo, año, versión, N° motor, N° chasis, color, tipo, combustible). Deja de tener dueño, estado, captador, sucursales, orden de venta y datos de venta.
- **Nueva tabla `actas_recepcion`:** el evento de corretaje. Referencia al vehículo y al cliente **dueño en ese momento**, más captador, sucursal de origen y de venta, km de ingreso, orden de venta, estado, fechas y cierre de venta. Un vehículo admite N actas históricas y **solo una activa a la vez**.
- **BREAKING — Checklist e historial migran al acta:** `vehiculo_checklist` → `acta_checklist` y `vehiculo_estado_historial` → `acta_estado_historial`. Cada recepción tiene su propio checklist de 12 puntos y su propia línea de tiempo de estados; los de una recepción anterior no se pisan.
- **Reingreso soportado:** al levantar un acta se hace get-or-create del vehículo por PPU (igual que hoy con el cliente por RUT). Si el auto ya tiene acta activa → 409; si existe sin acta activa → se reutiliza la ficha y se crea un acta nueva, conservando todo el historial.
- **Ciclo de vida del abono de exclusividad:** el abono deja de ser un entero suelto y pasa a tener estado explícito. Nace como **anticipo no devengado** al firmar; si la venta se concreta se **aplica a la comisión** (el cliente paga `comisión − abono` al cierre, conforme a la cláusula QUINTA del acta firmada) y se reconoce como ingreso; si el auto se vende externamente o el dueño desiste, la empresa lo **retiene** como ingreso por gestión (fotografía, publicidad). Esto habilita separar, para un dashboard futuro, el ingreso ya ganado del monto todavía comprometido.
- **Mantenedor de vehículos:** la ficha física pasa a ser editable de forma escalonada — el captador corrige mientras no haya actas firmadas; con historial documental solo `Management`/`TenantAdmin`/`SuperAdmin`, con motivo y auditoría, porque el cambio se propaga a documentos ya emitidos. Nueva entrada de menú "Vehículos" en el grupo de Validaciones y Catálogo.
- **Nueva pantalla `/actas`:** grilla con las actas del usuario autenticado por defecto, toggle "ver todas del tenant" para roles transversales (Management, TenantAdmin, SuperAdmin), y acción "Nueva acta" hacia `/actas/nueva`. `/actas/nueva` deja de ser el punto de entrada del módulo.
- **Migración de datos:** cada fila actual de `vehiculos` se divide en una ficha de vehículo más un acta, preservando ids, relaciones y estados existentes. Sin pérdida de información.

## Capabilities

### New Capabilities
- `abono-exclusividad`: Ciclo de vida y clasificación contable del abono de exclusividad — anticipo no devengado, aplicado a comisión o retenido por gestión — con los agregados que alimentan el dashboard financiero.

### Modified Capabilities
- `acta-recepcion`: El acta pasa a ser una entidad propia separada del vehículo; se admite más de una recepción por vehículo a lo largo del tiempo; checklist e historial de estado cuelgan del acta; se agrega la grilla `/actas` como entrada del módulo.
- `derivacion-venta`: `sucursal_id` y `sucursal_venta_id` se leen desde el acta, no desde el vehículo; la derivación aplica a una recepción concreta.
- `registro-venta`: La venta se registra contra el acta activa y cierra esa acta; al cerrarse se resuelve el abono de exclusividad.

## Impact

- **Base de datos:** nueva tabla `actas_recepcion`; `vehiculos` adelgazada a identidad física; `vehiculo_checklist` y `vehiculo_estado_historial` renombradas y re-apuntadas al acta; índice único parcial de acta activa por vehículo; campos de estado del abono. Migración de datos con backfill.
- **Backend:** `src/models/vehiculo.py` se divide en vehículo + acta; `src/routers/vehiculos.py` (creación, listado, detalle, lookup global, PATCH, PDF) se reorienta a actas; `src/services/acta_pdf.py` lee del acta; `src/seed.py` genera vehículo + acta.
- **APIs — BREAKING:** el recurso principal pasa de `/api/v1/vehiculos` a `/api/v1/actas` (crear, listar con `?mine`, detalle, PDF, aceptar términos). `/api/v1/vehiculos` queda como consulta de fichas e historial de actas por PPU.
- **Backoffice:** nueva página `/actas` (grilla); `NuevaActa` y `MisCaptaciones` se adaptan al nuevo contrato; el detalle muestra el historial de recepciones anteriores del auto.
- **Changes no archivadas afectadas:** `acta-pdf-corporativo` (el PDF pasa a leer del acta), `derivacion-venta-sucursal` (sucursales en el acta), `registro-venta` (cierre de acta + resolución del abono), `m1-tasacion-rapida` (la tasación sigue siendo previa al acta, sin cambio de contrato).
- **Diferido:** el dashboard financiero que consume los agregados del abono se especifica aparte; acá solo se dejan el modelo y los datos correctos para poder construirlo.
