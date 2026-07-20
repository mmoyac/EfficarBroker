## Context

Primer módulo de negocio (Módulo 2). Se decidió que el acta crea el vehículo directamente en `RECEPCIONADO` sin depender de Tasación (M1). Alcance completo (cliente + vehículo + checklist 12 puntos + orden de venta). La aceptación de términos se difiere a un botón manual (no hay n8n aún). Reutiliza el patrón de tenant efectivo y auditoría del core.

## Goals / Non-Goals

**Goals:**
- Levantar el acta en una sola operación transaccional, scopeada al tenant efectivo.
- Checklist de 12 puntos como catálogo (regla de catálogos), con estado/vencimiento por vehículo.
- Registrar captador (usuario que levanta el acta) y sucursal.
- Transición de estado con auditoría (`PROSPECTO`/nada → `RECEPCIONADO` → `CONTRATO_ACEPTADO`).
- Habilitar descarga de PDF de firma (Acta + Orden de Venta) desde `CONTRATO_ACEPTADO`.

**Non-Goals:**
- Tasación/scraping (M1), publicación y fotos (M3), visitas (M4), liquidación (M5).
- Trigger n8n de correo y validación de la respuesta textual del cliente.
- Edición avanzada del acta tras crearla (se podrá extender luego).

## Decisions

### D1 — `clientes` maestra reutilizable por RUT
El cliente se identifica por RUT único por tenant. Al crear el acta, si el RUT ya existe en el tenant se reutiliza (y se actualizan datos de contacto); si no, se crea. Evita duplicar propietarios recurrentes (relevante para la comisión de fidelidad de M5).

### D2 — `vehiculos` operacional con orden de venta embebida
Los datos de la orden de venta (precio pactado, vigencia_dias por defecto 30, abono de exclusividad por defecto 40000) se embeben en `vehiculos` en esta etapa; si crecen las condiciones comerciales se extraen a una tabla `ordenes_venta`. `estado_id` referencia el catálogo `estados_vehiculo`.

### D3 — Checklist como catálogo + detalle por vehículo
`checklist_items` (catálogo, 12 puntos, con `requiere_vencimiento`). `vehiculo_checklist` guarda por vehículo: presente (bool), estado (texto corto), fecha_vencimiento (nullable), observación. La creación del acta inserta las 12 filas.

### D4 — Creación transaccional del acta
`POST /vehiculos` hace en una transacción: get-or-create cliente, crea vehículo en `RECEPCIONADO`, inserta checklist, y registra auditoría (`estado_nuevo=RECEPCIONADO`). Si algo falla, rollback total.

### D5 — Autorización y scoping
`require_roles("Sales","Management","TenantAdmin")` (SuperAdmin pasa). Todo filtra por `get_effective_tenant_id`. `?mine=true` filtra por `captador_user_id = usuario actual` para "Mis Captaciones". PPU única por tenant (constraint) → 409 si repetida.

### D6 — Transición manual a CONTRATO_ACEPTADO
`POST /vehiculos/{id}/aceptar-terminos` valida que el estado actual sea `RECEPCIONADO`, cambia a `CONTRATO_ACEPTADO` y audita. Sustituye temporalmente el flujo n8n (correo + respuesta del cliente).

### D7 — Documento de firma imprimible
`GET /vehiculos/{id}/documento-firma` genera un PDF con Acta de Recepción + Orden de Venta, disponible desde `CONTRATO_ACEPTADO` para firma presencial del cliente cuando se traslada el vehículo para fotos/gestión comercial.

## Risks / Trade-offs

- **Orden de venta embebida** puede quedar corta si las condiciones se vuelven complejas → Mitigación: extraer a tabla propia cuando M5 lo requiera.
- **RUT sin validación de dígito verificador** → Mitigación: validación básica de formato ahora; DV chileno como mejora.
- **Sin fotos ni documentos adjuntos** (llegan en M3) → el acta queda como registro de datos; aceptable para esta etapa.
- **Transición de estado sin máquina de estados formal** → se valida el estado origen puntualmente; a futuro, un helper de transición centralizado.

## Open Questions

- ¿La vigencia (30 días) y el abono de exclusividad ($40.000) deben ser parámetros por tenant (config) en vez de defaults? — Por ahora defaults en el acta; parametrizable en M5/Configuración.
- ¿"Mis Captaciones" para Management/TenantAdmin muestra todo el tenant? — Sí: `?mine=true` es opcional; sin él se ve todo el tenant.
