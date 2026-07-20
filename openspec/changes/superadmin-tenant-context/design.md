## Context

El Módulo 0 dejó el SuperAdmin como rol transversal sin "tenant activo". Se requiere que el SuperAdmin pueda operar dentro de un tenant específico y alternar entre tenants o volver a una vista de plataforma. La regla dura del proyecto exige que el `tenant_id` provenga del token y no sea manipulable por el cliente.

## Goals / Non-Goals

**Goals:**
- SuperAdmin selecciona un tenant activo y su contexto de datos queda scopeado a ese tenant.
- El tenant activo es autoritativo (viaja en el token re-emitido), no un header manipulable.
- SuperAdmin mantiene una vista de plataforma (directorio de tenants) y puede entrar/salir/cambiar de tenant.
- `/auth/me` refleja el tenant activo para que el frontend muestre el contexto.

**Non-Goals:**
- ABM de tenants (alta/baja/edición) — se abordará en el módulo SaaS del SuperAdmin.
- Métricas de consumo por tenant.
- Cambiar el comportamiento de los roles no-SuperAdmin (siguen atados a su tenant propio).

## Decisions

### D1 — Re-emisión de token con claim `active_tenant_id`
`POST /auth/select-tenant {tenant_id}` valida que el solicitante sea SuperAdmin y que el tenant exista y esté activo, y devuelve un nuevo access token con `active_tenant_id`. `exit-tenant` re-emite sin ese claim. El refresh token no cambia.
- *Por qué:* coherente con "tenant_id desde el token, no del cliente"; auditable; el resto del backend no necesita lógica especial salvo resolver el tenant efectivo.
- *Alternativa descartada:* header `X-Active-Tenant` (contexto proveniente del cliente).

### D2 — Tenant efectivo en `get_current_tenant`
`TenantContext` expone `tenant_id` (efectivo), `is_platform` (True si SuperAdmin) y `active_tenant_id`. Resolución:
- Usuario normal: efectivo = `user.tenant_id`.
- SuperAdmin con `active_tenant_id` en token: efectivo = `active_tenant_id`.
- SuperAdmin sin selección: efectivo = `None` (vista plataforma).
Los futuros endpoints transaccionales filtran por `ctx.tenant_id`; si es `None` para SuperAdmin en vista plataforma, esos endpoints operativos exigen tenant activo (422/400) o se limitan a vistas de plataforma.

### D3 — Autorización de la selección
Solo SuperAdmin puede listar tenants y seleccionar. Se reutiliza `require_roles("SuperAdmin")` (SuperAdmin siempre pasa). Un no-SuperAdmin recibe 403.

### D4 — Frontend: vista plataforma + switcher
Tras login, si el rol es SuperAdmin y no hay tenant activo, el backoffice muestra la **vista de plataforma** (directorio de tenants para "entrar"). Al seleccionar, se guarda el token re-emitido, se invalida el menú/me y se navega al dashboard operando como el tenant. Un switcher en el layout muestra el tenant activo y permite cambiar o volver a plataforma. Los usuarios no-SuperAdmin no ven nada de esto.

## Risks / Trade-offs

- **Token re-emitido no invalida el anterior** (sin blacklist) → un token viejo sin tenant sigue válido hasta expirar. Mitigación: expiración corta del access token; el frontend usa siempre el último token. Aceptable en dev.
- **SuperAdmin en vista plataforma consulta endpoint operativo** (tenant efectivo None) → Mitigación: los endpoints transaccionales (M1+) validan que exista tenant efectivo y responden error claro si falta.
- **Refresh re-emite sin `active_tenant_id`** → tras refرescar, el SuperAdmin volvería a vista plataforma. Mitigación: incluir `active_tenant_id` también en el refresh, o re-seleccionar; para dev, `/refresh` preserva el claim si el refresh lo porta. Decisión: el refresh del SuperAdmin no porta tenant; el frontend re-selecciona si es necesario (simplicidad).

## Open Questions

- ¿El `active_tenant_id` debe persistir entre refrescos de token? — Por ahora no; el frontend mantiene la selección y re-selecciona si el token se renueva sin claim.
