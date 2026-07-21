## 1. Modelo de datos

- [x] 1.1 Catálogos en `src/models/catalogs.py`: `estados_abono` (`NO_DEVENGADO`, `APLICADO_COMISION`, `RETENIDO`), `motivos_cierre_acta` (`DESISTIMIENTO`, `VENTA_EXTERNA`), `tipos_checklist_item` (`DOCUMENTO`, `ACCESORIO`) y `estados_checklist` (`OK`, `FALTANTE`, `OBSERVADO`) — estos dos últimos reemplazan strings hardcodeados existentes
- [x] 1.2 Modelo `ActaRecepcion` en `src/models/acta.py`: `vehiculo_id`, `cliente_id`, `captador_user_id`, `sucursal_id`, `sucursal_venta_id`, `km_ingreso`, `estado_id`, `fecha_recepcion`, orden de venta (`precio_venta_pactado`, `vigencia_dias`, `exclusividad_abono`, `tipo_comision_id`), venta (`vendedor_user_id`, `precio_venta_final`, `fecha_venta`), cierre (`cerrada`, `motivo_cierre_id`, `fecha_cierre`) y abono (`estado_abono_id`, `fecha_cobro_abono`, `fecha_resolucion_abono`)
- [x] 1.3 Adelgazar `Vehiculo` a identidad física: quitar `cliente_id`, `captador_user_id`, `sucursal_id`, `sucursal_venta_id`, `estado_id`, `km_ingreso`, `tipo_comision_id`, orden de venta y datos de venta
- [x] 1.3b Quitar de `Vehiculo` las columnas de texto `marca` y `modelo` (derivarlas de `version_id`) y hacer `version_id` obligatoria; `color` pasa a FK de catálogo
- [x] 1.4 Renombrar `VehiculoChecklist` → `ActaChecklist` y `VehiculoEstadoHistorial` → `ActaEstadoHistorial`, re-apuntando la FK a `acta_id`; reemplazar `ChecklistItem.tipo` y `ActaChecklist.estado` (hoy strings libres) por FK a sus catálogos
- [x] 1.5 Relaciones: `Vehiculo.actas` (todas, ordenadas desc) y `ActaRecepcion.vehiculo`

## 2. Migración

- [x] 2.1 Migración Alembic `0010` (head actual: `0009_acta_corporativa`): crear `estados_abono`, `motivos_cierre_acta`, `actas_recepcion`, `acta_checklist`, `acta_estado_historial`
- [x] 2.2 Backfill: un acta por cada fila de `vehiculos`, preservando el `id` del vehículo como `id` del acta; `cerrada = (estado == VENDIDO)`; `estado_abono = APLICADO_COMISION` si vendida, `NO_DEVENGADO` si no
- [x] 2.3 Re-apuntar checklist e historial a `acta_id` y eliminar las tablas antiguas
- [x] 2.4 Eliminar de `vehiculos` las columnas migradas
- [x] 2.5 Índice único parcial `uq_acta_activa_por_vehiculo ON actas_recepcion(vehiculo_id) WHERE cerrada = false`
- [x] 2.6 `downgrade` que reconstruye las columnas de `vehiculos` desde el acta activa de cada vehículo
- [x] 2.7 Verificar la migración contra la base de desarrollo con datos de seed: conteos iguales, ninguna FK huérfana

## 3. Backend — actas

- [x] 3.1 Schemas `ActaCreate`, `ActaOut`, `ActaDetailOut`, `VehiculoFichaOut` en `src/schemas/`
- [x] 3.2 `POST /api/v1/actas`: get-or-create de cliente por RUT y de vehículo por PPU; `409` si el vehículo ya tiene acta activa; crea acta en `RECEPCIONADO` con checklist, orden de venta y abono en `NO_DEVENGADO`; auditoría
- [x] 3.3 `GET /api/v1/actas` con `?mine=true` y `?derivadas=true`; `GET /api/v1/actas/{id}` (detalle con checklist, cliente, vehículo y estado de abono)
- [x] 3.4 `POST /api/v1/actas/{id}/aceptar-terminos` (`RECEPCIONADO` → `CONTRATO_ACEPTADO`, `409` si no)
- [x] 3.5 `GET /api/v1/actas/{id}/documento-firma` desde `CONTRATO_ACEPTADO`
- [x] 3.6 `POST /api/v1/actas/{id}/registrar-venta`: valida vendedor por sucursal de venta, cierra el acta y transita el abono a `APLICADO_COMISION`
- [x] 3.7 `POST /api/v1/actas/{id}/cerrar-sin-venta`: motivo obligatorio, cierra el acta y transita el abono a `RETENIDO`; `409` si ya está cerrada
- [x] 3.8 Retirar de `/api/v1/vehiculos` los endpoints operativos, dejando la consulta de fichas

## 4. Backend — vehículos y abonos

- [x] 4.1 `GET /api/v1/vehiculos/{id}/actas`: historial de recepciones ordenado desc
- [x] 4.2 `GET /api/v1/vehiculos/lookup?ppu=`: ficha del vehículo en el tenant e indicador de si tiene acta activa, para precargar el formulario
- [x] 4.3 Mantener `GET /api/v1/vehiculos/lookup/vehiculo-global` leyendo el estado desde el acta más reciente
- [x] 4.4 `GET /api/v1/estados-abono` (catálogo)
- [x] 4.5 `GET /api/v1/abonos/resumen`: totales y conteos por estado de abono, filtrable por rango de fechas y sucursal, restringido a `Management`/`TenantAdmin`/`SuperAdmin`
- [x] 4.6 `src/services/acta_pdf.py` recibe el acta y navega a `acta.vehiculo`; el saldo de comisión al cierre descuenta el abono
- [x] 4.7 `src/seed.py`: generar vehículo + acta; agregar un vehículo con dos actas (una cerrada, una activa) para cubrir el caso de reingreso
- [x] 4.8 `PATCH /api/v1/vehiculos/{id}`: captador puede corregir mientras no haya actas firmadas ni cerradas; con historial documental solo `Management`/`TenantAdmin`/`SuperAdmin` con motivo obligatorio y auditoría; PPU solo esos roles
- [x] 4.9 `DELETE /api/v1/vehiculos/{id}`: `409` si el vehículo tiene alguna acta
- [x] 4.10 Registrar `/actas` en el menú (`menu_items`) como entrada del módulo, sobre `/actas/nueva`
- [x] 4.11 Entrada de menú "Vehículos" (`/vehiculos`) en el grupo de Validaciones y Catálogo, para `Management`

## 5. Backoffice

- [x] 5.1 Servicios y tipos TypeScript del recurso `actas`
- [x] 5.2 Página `/actas`: grilla con PPU, vehículo, cliente, estado, fecha de recepción y precio pactado; por defecto `?mine=true`; botón "Nueva acta"
- [x] 5.3 Toggle "ver todas del tenant" visible solo para `Management`/`TenantAdmin`/`SuperAdmin`, que agrega la columna de captador
- [x] 5.4 Estado vacío con invitación a crear la primera acta
- [x] 5.5 `NuevaActa`: al ingresar la PPU, consultar el lookup y precargar datos del vehículo advirtiendo el reingreso; bloquear si hay acta vigente
- [x] 5.6 Detalle del acta con checklist, orden de venta e historial de recepciones anteriores del vehículo
- [x] 5.7 Adaptar `MisCaptaciones` y `/captaciones/derivadas` al contrato de actas
- [x] 5.8 Mostrar comisión pactada, abono descontado y saldo neto al confirmar la venta
- [x] 5.9 Mantenedor `/vehiculos` para `Management`: grilla buscable por PPU, detalle con atributos físicos e historial de actas, y edición con advertencia de impacto y motivo obligatorio
- [x] 5.10 Rutas en `App.tsx`: `/actas` (grilla), `/actas/nueva`, `/actas/:id`, `/vehiculos`, `/vehiculos/:id`

## 6. Pruebas

- [x] 6.1 Reingreso: acta → venta → segunda acta del mismo vehículo con otro cliente; ambas coexisten con checklist e historial propios
- [x] 6.2 Segunda acta con acta vigente responde `409`
- [x] 6.3 Concurrencia: dos creaciones simultáneas para la misma PPU dejan una sola acta activa
- [x] 6.4 Aislamiento entre tenants en `/actas`, `/vehiculos/{id}/actas` y `/abonos/resumen`
- [x] 6.5 Abono: `NO_DEVENGADO` → `APLICADO_COMISION` al vender, `→ RETENIDO` al cerrar sin venta, `409` en transición inválida
- [x] 6.6 Abono mayor que la comisión deja saldo cero sin generar monto a favor del cliente
- [x] 6.7 `/abonos/resumen` separa comprometido de ganado y responde `403` a `Sales`
- [x] 6.8 El PDF de un acta histórica refleja el cliente y checklist de esa recepción
- [x] 6.9 Derivación y comisión cruzada aisladas por acta
- [x] 6.10 Migración `upgrade` + `downgrade` sobre la base de seed sin pérdida de datos

## 7. Refinamientos de prueba de usuario (jornada 2026-07-21)

- [x] 7.1 Migración `0011`: columna `observaciones` en `actas_recepcion`
- [x] 7.2 Sucursal de recepción por defecto (la del usuario); `400` si no tiene y no la envía
- [x] 7.3 Vendedor nominado al derivar: obligatorio y validado a la sucursal de venta; `equipo-ventas?sucursal_id=` filtra por sucursal
- [x] 7.4 Observaciones del acta capturadas y persistidas
- [x] 7.5 `PATCH /api/v1/actas/{id}` edita todo incluido el checklist (upsert por ítem), observaciones y vendedor
- [x] 7.6 `VehiculoFichaOut` expone `marca_id`/`modelo_id` para precargar la cascada en el reingreso
- [x] 7.7 PDF: "Firma Ejecutivo" = vendedor nominado (derivada) o captador (propia); columna de vencimiento separada; sección de observaciones
- [x] 7.8 Backoffice: autocomplete de RUT/PPU al escribir, sucursal implícita, selector de vendedor al derivar, edición completa del acta, textarea de observaciones
- [x] 7.9 Pruebas HTTP de los refinamientos (15 aserciones) + PDF con vendedor nominado, vencimiento y observaciones
