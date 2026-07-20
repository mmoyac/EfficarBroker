## 1. Backend — modelo y migración

- [x] 1.1 Agregar `sucursal_venta_id` (FK `sucursales`, NOT NULL, `ondelete=RESTRICT`, index) al modelo `Vehiculo`, con relationship `sucursal_venta` y docstring aclarando que `sucursal_id` es la de origen/captación
- [x] 1.2 Migración Alembic 0008 (`down_revision = 0007_vehiculo_catalogos`): add columna nullable → backfill `sucursal_venta_id = sucursal_id` → set NOT NULL + FK + índice; `downgrade` inverso
- [x] 1.3 Verificar `alembic upgrade head` y `downgrade` en Docker sin errores sobre datos existentes

## 2. Backend — acta (crear/editar)

- [x] 2.1 `ActaCreate`: agregar `sucursal_venta_id: int` (requerido); validar en `crear_acta` que pertenezca al tenant efectivo (400 si no)
- [x] 2.2 `crear_acta`: persistir `sucursal_venta_id`; si el cliente no lo envía distinto, es venta propia (= `sucursal_id`)
- [x] 2.3 `VehiculoUpdateIn` + `editar_vehiculo_recepcionado`: permitir cambiar `sucursal_venta_id` solo en estado `RECEPCIONADO`, validando tenant

## 3. Backend — visibilidad y venta

- [x] 3.1 `GET /vehiculos`: agregar filtro `?derivadas=true` — para `Sales` filtra `sucursal_venta_id == current.sucursal_id AND sucursal_id != sucursal_venta_id`; roles transversales ven todas las derivadas del tenant
- [x] 3.2 `registrar_venta`: validar `vendedor.sucursal_id == vehiculo.sucursal_venta_id` (400 si no coincide), además de las validaciones actuales
- [x] 3.3 Serializers `VehiculoOut`/`VehiculoDetailOut`: exponer `sucursal_venta` (nombre) y `derivado` (= `sucursal_venta_id != sucursal_id`)

## 4. Backend — seed

- [x] 4.1 Sembrar un vehículo derivado de ejemplo: captado en Rancagua con `sucursal_venta` Santiago (idempotente)

## 5. Backoffice

- [x] 5.1 `/actas/nueva`: toggle "La venta la realizo yo" / "Derivar la venta a otra sucursal"; al derivar, selector de sucursal de venta (sucursales del tenant distintas a la de origen); enviar `sucursal_venta_id`
- [x] 5.2 Tipos y servicio: `sucursal_venta`, `derivado` en el vehículo; parámetro `derivadas` en el listado
- [x] 5.3 Página `/captaciones/derivadas`: tabla de autos derivados a la sucursal del ejecutivo con acción "Registrar venta"; registrar ruta y opción de menú `Ventas Derivadas a mi Sucursal` (rol `Sales`)
- [x] 5.4 Mostrar badge "Derivado → {sucursal}" en `/captaciones` y en el detalle

## 6. Verificación

- [x] 6.1 Acta con venta propia → `derivado=false`; acta derivada Rancagua→Santiago → `derivado=true` sin vendedor
- [x] 6.2 `sucursal_venta_id` de otro tenant → 400; edición de sucursal de venta solo en `RECEPCIONADO`
- [x] 6.3 Bandeja derivadas: ejecutivo Santiago ve el auto derivado; ejecutivo Rancagua no; Management ve todas
- [x] 6.4 Registrar venta: vendedor Santiago (correcto) → `VENDIDO`; vendedor Rancagua (incorrecto) → 400; auditoría + historial registrados
- [x] 6.5 Confirmar captador y vendedor de sucursales distintas ambos registrados en el auto `VENDIDO`
