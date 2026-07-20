## 1. Backend — Tasación rápida

- [x] 1.1 Crear schemas de entrada/salida para simulación de tasación (`ppu`, `km`, y 3 precios)
- [x] 1.2 Crear router `tasacion` con `POST /api/v1/tasacion/simular`
- [x] 1.3 Registrar router en `main.py`
- [x] 1.4 Aplicar RBAC en endpoint (`Sales`/`Management`/`TenantAdmin`)

## 2. Backoffice — Pantalla /tasacion

- [x] 2.1 Crear servicio frontend para consumir `POST /tasacion/simular`
- [x] 2.2 Crear página `/tasacion` con formulario PPU + kilometraje
- [x] 2.3 Mostrar resultado con 3 tarjetas: Mercado, Retoma, Publicación sugerido
- [x] 2.4 Registrar ruta en `App.tsx` para reemplazar placeholder

## 3. Verificación

- [x] 3.1 Build de backoffice sin errores
- [x] 3.2 Compilación de backend sin errores de sintaxis

## 4. Pendientes para cierre completo de M1

- [x] 4.1 Persistir prospecto en tabla operacional con estado inicial `PROSPECTO`
- [x] 4.2 Exponer endpoint de creación/listado de prospectos de tasación
- [x] 4.3 Integrar scraping asíncrono con proveedor externo (feature-flag/dev fallback)
- [ ] 4.4 Incorporar agendamiento de inspección en sucursal desde tasación
- [ ] 4.5 Agregar pruebas automatizadas (backend + front) para flujo M1

## 5. Normalización de catálogos vehículo (marca/modelo/versión)

- [x] 5.1 Crear tablas catálogo `vehiculo_marcas`, `vehiculo_modelos`, `vehiculo_versiones` con jerarquía por FK
- [x] 5.2 Exponer endpoints de catálogos seleccionables (marca → modelo → versión)
- [x] 5.3 Ajustar tasación para trabajar con `version_id` en vez de texto libre
- [x] 5.4 Incorporar los catálogos en "Nueva Acta de Recepción" y persistir `version_id`

## 6. Módulo Catálogo Vehicular (SuperAdmin)

- [x] 6.1 Crear CRUD backend para `vehiculo_marcas`/`vehiculo_modelos`/`vehiculo_versiones` (solo SuperAdmin)
- [x] 6.2 Crear página backoffice de administración de catálogo vehicular
- [x] 6.3 Registrar ruta del módulo y opción de menú para SuperAdmin
