## Why

La empresa premia con menor comisión a los clientes que le confían varios vehículos, pero hoy ese beneficio depende del criterio del ejecutivo: `tipos_comision` trae Estándar 5% y Gold 3%, y quien levanta el acta elige a mano cuál aplicar. Eso hace el beneficio inconsistente entre ejecutivos y sucursales, imposible de auditar y opaco para el cliente, que no puede saber por qué le cobraron una tasa u otra.

La tabla `clientes` ya identifica unívocamente al cliente por RUT dentro del tenant, y con la separación de `actas_recepcion` cada operación queda atribuida a un cliente. Están los datos para que la regla la resuelva el sistema.

## What Changes

- **Tramos de fidelidad como catálogo administrable:** nueva maestra `tramos_fidelidad` (mínimo de vehículos vendidos, máximo opcional, `tipo_comision_id` resultante), editable por `TenantAdmin`. Configuración inicial: 0–1 vehículos previos vendidos → Estándar 5%; 2 o más → Gold 3%, es decir el beneficio aplica desde el tercer vehículo.
- **Conteo por cliente:** el tramo se determina por la cantidad de **vehículos vendidos** históricamente para ese cliente en el tenant (actas cerradas con venta concretada), sin ventana de tiempo. Las actas cerradas sin venta no suman.
- **Resolución automática al levantar el acta:** `POST /api/v1/actas` calcula el tramo del cliente y aplica el `tipo_comision` correspondiente. El ejecutivo ve la tasa resuelta y su justificación; ya no la elige libremente.
- **Tramo congelado en el acta:** el `tipo_comision_id` resuelto y el conteo que lo justificó se persisten en el acta al momento de crearla. Operaciones posteriores del cliente NO SHALL alterar actas ya levantadas — el cliente firmó un contrato con una comisión determinada.
- **Override supervisado:** `Management`/`TenantAdmin` pueden forzar un tipo de comisión distinto al resuelto, con motivo obligatorio y registro en auditoría. Los `Sales` no pueden.
- **Visibilidad del beneficio:** la ficha del cliente expone su historial de operaciones, su tramo actual y cuántos vehículos le faltan para el siguiente, para que el ejecutivo lo use comercialmente.

## Capabilities

### New Capabilities
- `fidelidad-cliente`: Tramos de fidelidad por volumen de vehículos vendidos por cliente, y resolución automática del tipo de comisión al levantar el acta.

### Modified Capabilities
- `acta-recepcion`: El tipo de comisión deja de elegirse libremente en el formulario y pasa a resolverse desde el tramo de fidelidad del cliente, congelándose en el acta.

## Impact

- **Depende de:** `vehiculo-entidad-fuerte`. El conteo se apoya en `actas_recepcion` cerradas con venta; sin esa separación no hay forma de contar operaciones por cliente sin contaminar el historial.
- **Base de datos:** nueva maestra `tramos_fidelidad` + seed inicial; campos `tipo_comision_resuelto_por` (tramo | override), `vehiculos_vendidos_al_firmar` y `motivo_override` en `actas_recepcion`.
- **Backend:** nuevo `src/services/fidelidad.py` con la resolución de tramo; `POST /api/v1/actas` la invoca; CRUD de `tramos_fidelidad`; `GET /api/v1/clientes/{id}/fidelidad`.
- **Backoffice:** `/actas/nueva` muestra la tasa resuelta y su justificación en lugar del selector libre; pantalla de administración de tramos para `TenantAdmin`; ficha de cliente con su historial y tramo.
- **Negocio:** el beneficio se vuelve uniforme y auditable entre ejecutivos y sucursales. Los ejecutivos pierden discrecionalidad sobre la tasa, lo que es el objetivo.
- **Diferido:** notificar al cliente cuando alcanza un tramo nuevo; tramos por tipo de vehículo o por monto acumulado en lugar de por unidades.
