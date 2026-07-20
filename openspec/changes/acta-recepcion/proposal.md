## Why

El corazón operativo del negocio es recibir físicamente un vehículo y formalizar el contrato de corretaje (Módulo 2). Hoy un ejecutivo de ventas ve la opción "Nueva Acta de Recepción" pero cae en un placeholder. Este cambio habilita al ejecutivo a levantar el acta: registrar al cliente y su vehículo, completar el checklist de 12 puntos, pactar la orden de venta y dejar el auto en estado `RECEPCIONADO`, quedando registrado el captador y la sucursal.

## What Changes

- **Modelo de datos del acta:**
  - `clientes` (maestra, por tenant): RUT, nombre, correo, teléfono.
  - `vehiculos` (operacional, por tenant): PPU, marca, modelo, año, N° motor, N° chasis, km de ingreso, `estado_id` (→ `estados_vehiculo`), `cliente_id`, `captador_user_id`, `sucursal_id`, y orden de venta (precio pactado, vigencia en días, abono de exclusividad), fecha de recepción.
  - `checklist_items` (catálogo): los 12 puntos de documentos/accesorios (con indicador de si requieren vencimiento).
  - `vehiculo_checklist` (operacional): estado y fecha de vencimiento de cada punto para un vehículo.
- **Endpoints:**
  - `GET /api/v1/checklist-items` — catálogo de los 12 puntos para el formulario.
  - `POST /api/v1/vehiculos` — crea el acta: cliente (reutiliza por RUT), vehículo en `RECEPCIONADO`, checklist y orden de venta; captador = usuario autenticado; registra auditoría.
  - `GET /api/v1/vehiculos` (lista del tenant; `?mine=true` para "Mis Captaciones") y `GET /api/v1/vehiculos/{id}` (detalle con checklist).
  - `POST /api/v1/vehiculos/{id}/aceptar-terminos` — botón manual que transita el auto a `CONTRATO_ACEPTADO` (n8n/correo diferido).
- **Reglas:** todo scopeado al tenant efectivo; PPU única por tenant; el acta la levantan `Sales`/`Management`/`TenantAdmin`; cada mutación de estado genera log en `logs_auditoria`.
- **Backoffice:** página "Nueva Acta de Recepción" (`/actas/nueva`) con el formulario completo, y "Mis Captaciones" (`/captaciones`) con la lista de autos del ejecutivo y la acción de aceptar términos.

## Capabilities

### New Capabilities
- `acta-recepcion`: Levantamiento del acta de recepción que crea cliente + vehículo en `RECEPCIONADO`, con checklist de 12 puntos y orden de venta, y transición manual a `CONTRATO_ACEPTADO`.

### Modified Capabilities
<!-- Ninguna delta sobre specs archivadas: capacidad nueva. -->

## Impact

- **Base de datos:** tablas `clientes`, `vehiculos`, `checklist_items`, `vehiculo_checklist` (migración 0003) + seed de los 12 checklist items.
- **APIs nuevas:** `/checklist-items`, `/vehiculos` (crear/listar/detalle), `/vehiculos/{id}/aceptar-terminos`.
- **Backend:** primer flujo de negocio con transición de estados + auditoría; reutiliza el scoping por tenant efectivo.
- **Backoffice:** formulario de acta + página de captaciones.
- **Diferido:** motor de scraping/tasación (M1), trigger n8n de correo y respuesta "ACEPTO LOS TÉRMINOS" del cliente, fotos profesionales (M3).
