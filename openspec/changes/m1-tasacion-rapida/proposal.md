## Why

M1 (Tasación e Inteligencia de Mercado) es el punto de entrada del ciclo comercial. La ruta /tasacion existía en el menú de Sales pero caía en placeholder, impidiendo capturar PPU + kilometraje y obtener una referencia inicial de precios. Este cambio formaliza la implementación de Tasación Rápida y deja trazado el camino para evolucionar a scraping asíncrono y persistencia completa del prospecto.

## What Changes

- Backend:
  - Nuevo endpoint `POST /api/v1/tasacion/simular` para estimar:
    - Precio Mercado
    - Precio Retoma
    - Precio Publicación Sugerido
  - Restringido a roles `Sales`/`Management`/`TenantAdmin` (SuperAdmin transversal).
- Backoffice:
  - Nueva vista `/tasacion` con formulario de entrada (PPU + kilometraje).
  - Render de resultados en tres tarjetas de precios.
- OpenSpec:
  - Se agrega capability nueva `tasacion` con requisitos de entrada/salida y control de acceso.

## Capabilities

### New Capabilities
- `tasacion`: Tasación rápida por PPU y kilometraje con tres umbrales de precio.

### Modified Capabilities
- Ninguna.

## Impact

- APIs nuevas:
  - `/api/v1/tasacion/simular`
- UI nueva:
  - `/tasacion`
- Alcance actual:
  - Simulación interna determinística (sin scraping externo ni persistencia de prospecto).
- Alcance diferido para completar M1:
  - Persistencia de prospecto en estado `PROSPECTO`.
  - Integración de scraping asíncrono (fuentes tipo Chileautos).
  - Agendamiento de inspección en sucursal desde la tasación.
