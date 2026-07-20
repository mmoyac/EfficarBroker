## Context

M1 define captura inicial de vehículo con PPU y kilometraje para generar una referencia comercial. En esta iteración se prioriza una primera entrega funcional end-to-end para habilitar operación de Sales en backoffice y preparar la extensión hacia scraping real.

## Goals / Non-Goals

**Goals:**
- Habilitar ruta `/tasacion` con formulario operativo.
- Exponer endpoint backend de simulación con salida de 3 precios.
- Aplicar RBAC y autenticación en el endpoint.
- Dejar especificación trazable en OpenSpec.

**Non-Goals (esta iteración):**
- Scraping a proveedores externos.
- Persistencia de prospecto en BD.
- Flujo de agendamiento de inspección.
- Motor avanzado de pricing con variables de marca/modelo/versión/año.

## Decisions

### D1 — Endpoint de simulación dedicado
Se define `POST /api/v1/tasacion/simular` para encapsular el cálculo y desacoplarlo de futuros endpoints de tasación completa.

### D2 — Modelo de salida explícito de 3 precios
La respuesta expone exactamente los tres umbrales del módulo de negocio para alinear lenguaje de front y operaciones.

### D3 — Cálculo determinístico interno (temporal)
Se implementa una fórmula interna reproducible en función de PPU y kilometraje para entregar resultados consistentes mientras no exista scraping.

### D4 — Seguridad por rol
Solo roles operativos internos (`Sales`, `Management`, `TenantAdmin`) ejecutan tasación rápida; el control se aplica con `require_roles`.

## Risks / Trade-offs

- Sin scraping real, la referencia puede diferir del mercado.
- Sin persistencia, la tasación no deja historial transaccional todavía.
- Fórmula simple puede requerir recalibración al conectar datos reales.

## Open Questions

- ¿La tasación rápida debe crear automáticamente un prospecto en estado `PROSPECTO`?
- ¿Qué proveedor externo se prioriza primero para scraping y con qué frecuencia?
- ¿Se requiere versionar la fórmula de pricing por tenant?
