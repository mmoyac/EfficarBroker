## Context

`tipos_comision` ya existe como catálogo con `tasa` y `minimo`, y `calcular_comision` aplica `MAX(precio × tasa, minimo)` ([backend/src/utils/comision.py:10-15](../../../backend/src/utils/comision.py#L10-L15)). El seed trae Estándar 5% y Gold 3%. La pieza que falta no es el cálculo sino **quién decide qué tipo aplica**: hoy lo elige el ejecutivo en el formulario, con `tipo_comision_id` viajando como dato libre en el body ([backend/src/routers/vehiculos.py:167](../../../backend/src/routers/vehiculos.py#L167)).

Eso convierte un beneficio comercial en discrecionalidad individual: dos clientes con el mismo historial pueden terminar con tasas distintas según quién los atendió, sin registro de por qué.

`clientes` ya es maestra por tenant con unique `(tenant_id, rut)` ([backend/src/models/cliente.py:13](../../../backend/src/models/cliente.py#L13)), así que la identidad del cliente está resuelta. Lo que habilita este cambio es `vehiculo-entidad-fuerte`: sin actas separadas no se puede contar operaciones por cliente, porque el historial de un vehículo recepcionado dos veces vive hoy en una sola fila que se pisa.

## Goals / Non-Goals

**Goals:**
- Que el beneficio por volumen lo resuelva el sistema, uniforme entre ejecutivos y sucursales.
- Umbrales administrables por `TenantAdmin` sin tocar código.
- Trazabilidad: por qué este acta tiene esta tasa.
- Permitir excepción comercial, pero supervisada y registrada.

**Non-Goals:**
- Rediseñar `calcular_comision`. La fórmula no cambia; cambia de dónde sale el `tipo_comision`.
- Tramos por monto acumulado, por tipo de vehículo o con vencimiento. Se parte por unidades vendidas.
- Notificar al cliente al alcanzar un tramo.
- Unificar clientes con el mismo RUT entre tenants. El aislamiento por fila se mantiene.

## Decisions

### 1. Tramo → `tipo_comision`, no un descuento sobre la tasa

`tramos_fidelidad` apunta a un `tipo_comision` existente en lugar de aplicar un porcentaje de descuento sobre la tasa.

Alternativa descartada: descuento porcentual sobre la tasa base (ej. −20% sobre 5% = 4%). Habría introducido una segunda dimensión de cálculo, tasas efectivas que no existen en ningún catálogo y un `minimo` ambiguo — ¿se descuenta también el piso en CLP? Apuntar a un tipo ya definido mantiene una sola fuente de verdad para toda tasa que el sistema puede cobrar.

### 2. Cuentan vehículos **vendidos**, no ingresados

El conteo suma actas cerradas con venta concretada. Una acta cerrada sin venta (desistimiento o venta externa) no suma, aunque el auto haya entrado físicamente.

Alternativa descartada: contar ingresos. Es más fácil de explicar y de aplicar al firmar, pero premiaría a un cliente que ingresa autos y los retira sin que la empresa gane un peso — el beneficio existe para retribuir negocio hecho, no intención.

Consecuencia asumida: el cliente que ingresa su tercer auto teniendo dos vigentes sin vender aún **no** accede al beneficio. Es coherente con el criterio, pero conviene que Comercial lo sepa antes de comunicarlo.

### 3. Conteo de por vida, sin ventana temporal

Premia la relación de largo plazo y evita que un cliente pierda su beneficio por inactividad, lo que sería difícil de defender frente a él. También simplifica el cálculo: un `COUNT` sobre actas vendidas del cliente, sin aritmética de fechas ni recálculos periódicos.

### 4. El tramo se congela en el acta al crearla

`actas_recepcion` persiste `tipo_comision_id`, `vehiculos_vendidos_al_firmar` y `tipo_comision_resuelto_por` (`TRAMO` | `OVERRIDE`).

Esta es la decisión menos negociable del diseño: la comisión es una cláusula del contrato que el cliente firma y que se imprime en el PDF. Derivarla en tiempo de lectura haría que un acta firmada al 5% apareciera al 3% después de que el cliente venda otro auto — el documento impreso y el sistema dirían cosas distintas. Guardar el conteo junto al tipo permite además auditar la decisión sin reconstruir el estado histórico del cliente.

Por lo mismo, cambiar la configuración de tramos afecta solo actas futuras.

### 5. `tipo_comision_id` deja de aceptarse como dato libre

El body de `POST /api/v1/actas` deja de recibirlo de `Sales`. Solo `Management`/`TenantAdmin` pueden enviarlo, y en ese caso el motivo es obligatorio y se marca como `OVERRIDE`.

Alternativa descartada: seguir aceptándolo y solo advertir en la UI cuando difiere del resuelto. La regla se cumpliría únicamente en el frontend; cualquier llamada directa a la API la saltaría, y el beneficio volvería a ser inconsistente.

### 6. Validación de cobertura de tramos al guardar

Los tramos deben cubrir todo el rango de conteos sin solapes ni huecos. Sin esa validación, un conteo sin tramo asignado dejaría al acta sin tipo de comisión y rompería la creación en producción. Se valida el conjunto completo en cada escritura, no el tramo aislado.

## Risks / Trade-offs

- **El ejecutivo pierde una herramienta de negociación** → Es el objetivo explícito, pero tiene costo comercial real. El override para `Management` es la válvula de escape; conviene revisar en auditoría con qué frecuencia se usa: mucho uso significa que los tramos están mal calibrados.

- **Un cliente puede quedar a un auto del beneficio y no saberlo** → `GET /api/v1/clientes/{id}/fidelidad` expone cuántos vehículos faltan para el siguiente tramo, para que el ejecutivo lo use como argumento de venta.

- **Clientes duplicados por RUT mal digitado inflan o fragmentan el conteo** → El get-or-create por RUT ya existe, pero no hay normalización ni validación del dígito verificador. Un RUT tipeado con formato distinto crea un cliente nuevo y el historial se parte. Fuera de alcance acá, pero es una debilidad concreta que conviene atacar antes de que el conteo tenga consecuencias monetarias.

- **Costo del `COUNT` en cada creación de acta** → Es una operación por acta creada, sobre índice de `cliente_id`. Volumen despreciable; no se cachea.

- **Los tramos son por tenant y el seed los crea iguales para todos** → Cada tenant puede calibrarlos después. No se contempla heredar configuración de plataforma.

## Migration Plan

1. Migración Alembic posterior a la de `vehiculo-entidad-fuerte`: crear `tramos_fidelidad` y agregar a `actas_recepcion` los campos de trazabilidad.
2. Seed de tramos iniciales por tenant: `0–1` → Estándar, `2+` → Gold.
3. Backfill de actas existentes: `vehiculos_vendidos_al_firmar` calculado desde el historial del cliente y `tipo_comision_resuelto_por = OVERRIDE` (fueron elegidas a mano, y marcarlas como resueltas por tramo sería falsear el registro).
4. Endurecer `POST /api/v1/actas` y actualizar el backoffice en el mismo despliegue.

## Open Questions

- ¿El umbral de 3 vehículos y la tasa Gold 3% son los definitivos, o hay más tramos previstos (5+, 10+)? La maestra los admite sin migración; solo hay que definirlos.
- ¿El beneficio debería considerar también los vehículos que el cliente **compró** a través de la empresa, no solo los que vendió? Hoy no se modela al comprador como cliente; sería un cambio mayor.
- ¿Qué debe pasar si `TenantAdmin` baja un umbral y clientes que ya firmaron habrían calificado? El diseño dice que no se recalcula; confirmar que Comercial está de acuerdo con no aplicar retroactividad.
