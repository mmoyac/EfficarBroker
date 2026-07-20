## 1. Backend — modelo de datos

- [x] 1.1 Modelar catálogo `checklist_items` (code, nombre, tipo, requiere_vencimiento, orden)
- [x] 1.2 Modelar maestra `clientes` (tenant_id, rut, nombre, email, telefono; RUT único por tenant)
- [x] 1.3 Modelar operacional `vehiculos` (tenant_id, ppu única por tenant, marca, modelo, anio, n_motor, n_chasis, km_ingreso, estado_id, cliente_id, captador_user_id, sucursal_id, precio_venta_pactado, vigencia_dias, exclusividad_abono, fecha_recepcion)
- [x] 1.4 Modelar operacional `vehiculo_checklist` (vehiculo_id, checklist_item_id, presente, estado, fecha_vencimiento, observacion)
- [x] 1.5 Migración Alembic 0003 con las 4 tablas y sus FK/constraints
- [x] 1.6 Historial de estados para KPIs: tabla `vehiculo_estado_historial` (vehiculo_id, estado_id, user_id, timestamp) + migración 0004; se registra en cada transición

## 2. Backend — seed y catálogo

- [x] 2.1 Seed de los 12 `checklist_items` con `requiere_vencimiento` donde aplique
- [x] 2.2 `GET /api/v1/checklist-items` autenticado

## 3. Backend — endpoints del acta

- [x] 3.1 Schemas: `ActaCreate` (cliente, vehículo, orden de venta, checklist[]), `VehiculoOut`, `VehiculoDetailOut`
- [x] 3.2 `POST /api/v1/vehiculos` transaccional: get-or-create cliente por RUT, crea vehículo en `RECEPCIONADO`, inserta checklist, captador = usuario; auditoría + historial; 409 si PPU repetida; roles Sales/Management/TenantAdmin; tenant efectivo
- [x] 3.3 `GET /api/v1/vehiculos` (tenant; `?mine=true` por captador) y `GET /api/v1/vehiculos/{id}` (detalle + checklist; 404 cross-tenant)
- [x] 3.4 `POST /api/v1/vehiculos/{id}/aceptar-terminos` (RECEPCIONADO → CONTRATO_ACEPTADO; 409 si no aplica; auditoría + historial)

## 4. Backoffice

- [x] 4.1 Tipos y servicios (checklist-items, crear acta, listar/detalle vehículos, aceptar términos)
- [x] 4.2 Página `/actas/nueva`: formulario cliente + vehículo + orden de venta + checklist de 12 puntos
- [x] 4.3 Página `/captaciones`: tabla de vehículos (estado, PPU, cliente) con acción "Aceptar términos"; rutas registradas
- [x] 4.4 Feedback de errores (PPU duplicada, validaciones) y navegación tras crear

## 5. Verificación

- [x] 5.1 Crear un acta como Sales → vehículo en RECEPCIONADO en Mis Captaciones; PPU duplicada → 409; reutilización de cliente por RUT
- [x] 5.2 Aceptar términos → CONTRATO_ACEPTADO + auditoría + historial; aislamiento entre tenants (404); Marketing → 403; historial con timestamps verificado

## 6. Documento de firma (PDF Acta + Orden)

- [x] 6.1 Endpoint `GET /api/v1/vehiculos/{id}/documento-firma` (disponible desde `CONTRATO_ACEPTADO`)
- [ ] 6.2 Definir plantilla visual corporativa del PDF (cabecera, jerarquía de secciones, pie legal)
- [ ] 6.3 Ajustar layout final para impresión y validación con usuarios de negocio
