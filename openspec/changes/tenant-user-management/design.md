## Context

Con el SuperAdmin ya capaz de entrar a un tenant, se habilita la administración del equipo del tenant y el licenciamiento SaaS. Es el primer conjunto de endpoints transaccionales, por lo que ejercita por primera vez el filtro real por `tenant_id` (tenant efectivo del contexto).

## Goals / Non-Goals

**Goals:**
- CRUD de usuarios scopeado al tenant efectivo, con rol y sucursal por FK a catálogo/maestra.
- Cupo de usuarios por tenant definido por el SuperAdmin (número o ilimitado) y validado al crear/reactivar.
- Aislamiento estricto: nadie ve ni toca usuarios de otro tenant.

**Non-Goals:**
- Planes con nombre (Básico/Pro): por ahora el cupo es una cantidad libre; si se requieren planes se añade un catálogo `planes`.
- Flujo de invitación por email / verificación (password inicial fija `admin123` en dev).
- Facturación real del SaaS.

## Decisions

### D1 — Cupo como columna `tenants.max_usuarios` (nullable = ilimitado)
Se agrega `max_usuarios INTEGER NULL` a `tenants`. `NULL` significa ilimitado; un entero es el tope de usuarios **activos**. Solo el SuperAdmin lo edita vía `PATCH /tenants/{id}`.
- *Alternativa:* catálogo `planes` con cupos fijos. Descartado ahora porque el usuario describe compra de cantidad flexible; migrable luego sin romper.

### D2 — Validación de cupo sobre usuarios activos
Al crear un usuario, o al reactivar uno desactivado, se cuenta `users` con `activo=True` del tenant; si `max_usuarios` no es NULL y el conteo alcanzó el tope, se responde `409`. Desactivar libera un cupo. El SuperAdmin, al reducir el cupo por debajo del uso actual, no desactiva usuarios automáticamente (solo impide crear/reactivar hasta que baje el uso).

### D3 — Scoping por tenant efectivo
Todos los endpoints de `users`, `roles` asignables y `sucursales` usan `get_current_tenant().tenant_id` como filtro obligatorio. Si el tenant efectivo es `None` (SuperAdmin en vista plataforma), los endpoints de usuarios responden `409` pidiendo seleccionar un tenant. Este es el patrón que reutilizarán los futuros módulos transaccionales.

### D4 — Autorización
`require_roles("TenantAdmin")` protege el CRUD de usuarios (SuperAdmin pasa por transversalidad). `PATCH /tenants/{id}` usa `require_roles("SuperAdmin")` estricto: el TenantAdmin NO puede tocar el cupo.

### D5 — Roles asignables
`GET /roles` retorna los roles asignables dentro de un tenant, excluyendo `SuperAdmin`. La creación/edición rechaza asignar `SuperAdmin` (400).

## Risks / Trade-offs

- **Reducir el cupo por debajo del uso** deja el tenant "sobre-asignado" → Mitigación: no se desactivan usuarios; solo se bloquean altas hasta regularizar. Se muestra uso/límite para visibilidad.
- **Condición de carrera en el conteo de cupo** (dos altas simultáneas) → Aceptable en dev; a futuro, verificación atómica / constraint.
- **Auto-desactivación** dejaría al tenant sin admin → Mitigación: se prohíbe desactivar la propia cuenta.

## Open Questions

- ¿El cupo cuenta usuarios activos o todos los creados? — Decisión: **activos** (desactivar libera cupo).
- ¿Debe existir un rol mínimo obligatorio (al menos un TenantAdmin activo)? — Deseable; se puede reforzar luego (no bloquea este change).
