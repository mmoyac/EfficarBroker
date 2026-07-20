## Context

`vehiculos` nació en `acta-recepcion` como una tabla única que resolvía el flujo completo del Módulo 2. Funcionó porque el caso de uso implícito era "un auto entra una vez, se vende una vez". Las changes posteriores (`derivacion-venta-sucursal`, `registro-venta`, `acta-pdf-corporativo`) siguieron colgando campos de la misma fila, y hoy `Vehiculo` tiene 25 columnas que responden a cuatro preguntas distintas: qué auto es, de quién es, qué se pactó y cómo terminó.

El síntoma concreto está en [backend/src/models/vehiculo.py:33](../../../backend/src/models/vehiculo.py#L33) — `UniqueConstraint("tenant_id","ppu")` — y en [backend/src/routers/vehiculos.py:149](../../../backend/src/routers/vehiculos.py#L149), que responde 409 al reingreso. El auto es un bien durable que rota entre dueños; el corredor querrá corretearlo de nuevo. Hoy no puede.

Un segundo hueco: `exclusividad_abono` es un `Integer` sin ciclo de vida ([vehiculo.py:80](../../../backend/src/models/vehiculo.py#L80)). La cláusula QUINTA del acta firmada ([acta_pdf.py:226-228](../../../backend/src/services/acta_pdf.py#L226-L228)) define tres desenlaces posibles para ese dinero, y el modelo no representa ninguno.

Restricciones: el sistema ya está corriendo con datos reales de seed y un flujo pendiente de prueba de usuario. Aislamiento por fila con `tenant_id` según AGENTS.md. La convención dura del proyecto exige que todo enum viva en tabla catálogo.

## Goals / Non-Goals

**Goals:**
- Permitir N recepciones del mismo vehículo a lo largo del tiempo, sin pérdida ni contaminación de historial.
- Separar identidad física del auto (`vehiculos`) del evento de corretaje (`actas_recepcion`).
- Dar al abono de exclusividad un ciclo de vida explícito que permita distinguir ingreso ganado de monto comprometido.
- Entregar `/actas` como grilla de entrada del módulo.
- Migrar los datos existentes sin pérdida.

**Non-Goals:**
- Construir el dashboard financiero. Acá solo se dejan el modelo y el endpoint de agregados; la visualización se especifica aparte.
- Compartir vehículos entre tenants. Se descartó explícitamente (ver Decisiones).
- Rediseñar el motor de comisiones. El cálculo de comisión se mantiene; solo se le suma el descuento del abono al cierre.
- Tocar `m1-tasacion-rapida`: la tasación es previa al acta y su contrato no cambia.

## Decisions

### 1. Dos tablas, no herencia ni columnas nullables

`vehiculos` conserva solo identidad física. `actas_recepcion` toma cliente, captador, sucursales, km de ingreso, orden de venta, estado, fechas y venta.

Alternativa descartada: dejar todo en `vehiculos` y agregar una columna `version_recepcion` con clave compuesta. Habría duplicado la ficha del auto en cada reingreso, que es exactamente el problema que se busca eliminar — motor y chasis no cambian entre recepciones.

`km_ingreso` se va al acta: sí varía entre recepciones y es un dato del momento de la entrega.

### 2. Vehículo por tenant, no global

`vehiculos` mantiene `tenant_id` y `UniqueConstraint(tenant_id, ppu)`.

Alternativa descartada: ficha global compartida entre tenants. Habría dado trazabilidad total del auto entre corredores, pero rompe el aislamiento por fila de AGENTS.md y expone a un tenant que el auto pasó por la competencia. El `GET /lookup/vehiculo-global` existente ([vehiculos.py:260](../../../backend/src/routers/vehiculos.py#L260)) se mantiene como consulta informativa cross-tenant, sin convertirse en modelo compartido.

### 3. Acta activa garantizada por índice único parcial

```sql
CREATE UNIQUE INDEX uq_acta_activa_por_vehiculo
  ON actas_recepcion (vehiculo_id) WHERE cerrada = false;
```

La invariante vive en la base, no en la aplicación. Una validación solo en el router es vulnerable a dos requests concurrentes; el índice parcial de PostgreSQL cierra esa ventana. `cerrada` es booleano derivado del cierre explícito (venta o cierre sin venta), no del `estado_id`, para que agregar estados nuevos al catálogo no invalide el índice.

### 4. `cerrada` como columna, no como consulta sobre el catálogo de estados

Tentador: `WHERE estado_id NOT IN (SELECT id FROM estados_vehiculo WHERE terminal)`. No sirve — PostgreSQL exige que el predicado de un índice parcial sea inmutable, y una subconsulta no lo es. Por eso el booleano explícito, seteado por los endpoints de cierre.

### 5. El recurso principal pasa a ser `/api/v1/actas`

`/api/v1/vehiculos` queda para consultar fichas e historial (`GET /vehiculos/{id}/actas`). Todo lo operativo — crear, listar, aceptar términos, PDF, registrar venta — se mueve a `/actas`.

Es un cambio breaking de API. Se acepta por ser un sistema pre-producción con un solo consumidor (el backoffice, que se actualiza en la misma change) y porque mantener `/vehiculos` para operar sobre actas dejaría un nombre que miente sobre lo que hace.

### 6. Abono como catálogo de estados con tres desenlaces

`estados_abono`: `NO_DEVENGADO` → `APLICADO_COMISION` | `RETENIDO`. Sigue la convención dura de catálogos del proyecto.

La decisión de fondo, confirmada con el usuario contra la cláusula QUINTA: **el abono es un anticipo de comisión, no un depósito reembolsable en efectivo.** Al vender, el cliente paga `comisión − abono` al cierre; no hay salida de caja. La distinción importa para el dashboard: mientras el acta está vigente el abono es dinero cobrado pero no devengado, y solo se reconoce como ingreso al resolverse en alguno de los dos desenlaces terminales.

Se descartó modelar una devolución en efectivo: contradice el contrato que el cliente firma.

### 7. Checklist e historial migran al acta

`vehiculo_checklist` → `acta_checklist`, `vehiculo_estado_historial` → `acta_estado_historial`. Sin esto, el segundo checklist del mismo auto pisaría al primero y `vehiculo_estado_historial` mezclaría en una sola línea de tiempo dos ciclos de vida distintos, arruinando los KPIs de duración por estado.

## Risks / Trade-offs

- **Migración con reasignación de ids** → La migración crea `actas_recepcion` preservando el `id` del vehículo original como `id` del acta (relación 1:1 en el momento del corte). Así las FKs existentes en checklist e historial se re-apuntan con un UPDATE directo, sin tabla de mapeo. Los ids de `vehiculos` no cambian.

- **API breaking con backoffice desplegado** → Backend y backoffice se despliegan juntos; no hay clientes externos. La migración de datos corre antes del cambio de rutas.

- **El PDF de actas históricas debe reflejar su propia recepción** → `acta_pdf.py` pasa a recibir el acta y navegar a `acta.vehiculo`, en lugar de recibir el vehículo. Cubierto por escenario de spec.

- **Superficie de cambio amplia (4 capabilities tocadas)** → Es el costo real de haber conflacionado las entidades desde el principio; crece si se posterga. Se hace ahora, antes de que existan más datos productivos.

- **Doble fuente de verdad transitoria durante la migración** → La migración es una sola transacción Alembic: crear tablas, copiar, re-apuntar FKs, eliminar columnas migradas de `vehiculos`. Rollback = `alembic downgrade`, que reconstruye las columnas desde el acta activa de cada vehículo (las actas históricas se perderían al revertir; aceptable porque al momento del corte no existen).

- **`estados_abono` puede necesitar más estados** (abono condonado, pagado en cuotas) → Es tabla catálogo, precisamente para admitirlos sin migración de esquema.

## Migration Plan

1. Migración Alembic `0007`: crear `estados_abono`, `actas_recepcion`, `acta_checklist`, `acta_estado_historial`.
2. Backfill: una fila en `actas_recepcion` por cada `vehiculos`, con `id` preservado, `cerrada = (estado = VENDIDO)`, `estado_abono = APLICADO_COMISION` si vendida y `NO_DEVENGADO` si no.
3. Re-apuntar checklist e historial al acta; eliminar tablas viejas.
4. Eliminar de `vehiculos` las columnas migradas; crear el índice único parcial.
5. Actualizar backend (modelos, routers, servicios, seed) y backoffice en el mismo despliegue.

## Open Questions

- ¿Qué motivos concretos de cierre sin venta debe ofrecer el catálogo? Se parte con `DESISTIMIENTO` y `VENTA_EXTERNA`; a confirmar con el equipo comercial.
- ¿Un acta vencida (superada su vigencia sin renovación) debe cerrarse automáticamente? La cláusula TERCERA dice que la vigencia se renueva automáticamente, así que por ahora no se cierra sola. A revisar si el negocio quiere expiración real.
- ¿El resumen de abonos debe segmentarse también por captador, o basta por sucursal y fecha? Depende del diseño del dashboard, que se especifica aparte.
