## 1. Modelo y migración

- [ ] 1.1 Maestra `TramoFidelidad` (por tenant): `nombre`, `min_vehiculos_vendidos`, `max_vehiculos_vendidos` (nullable), `tipo_comision_id`, `activo`
- [ ] 1.2 Catálogo `origenes_tipo_comision` (`TRAMO`, `OVERRIDE`) — no persistir el origen como texto libre
- [ ] 1.3 Campos de trazabilidad en `actas_recepcion`: `vehiculos_vendidos_al_firmar`, `origen_tipo_comision_id` (FK), `motivo_override`
- [ ] 1.4 Migración Alembic (posterior a la de `vehiculo-entidad-fuerte`) con seed de tramos: `0–1` → Estándar 5%, `2+` → Gold 3%
- [ ] 1.5 Backfill de actas existentes: conteo calculado desde el historial del cliente y origen `OVERRIDE`

## 2. Servicio de fidelidad

- [ ] 2.1 `src/services/fidelidad.py`: `contar_vehiculos_vendidos(db, cliente_id, tenant_id)` sobre actas cerradas con venta
- [ ] 2.2 `resolver_tramo(db, tenant_id, conteo)` que devuelve tramo y `tipo_comision`
- [ ] 2.3 Validador de cobertura del conjunto de tramos: sin solapes ni huecos
- [ ] 2.4 Pruebas unitarias del servicio con los casos borde de umbral (0, 1, 2, 3)

## 3. Backend — endpoints

- [ ] 3.1 CRUD `GET/POST/PATCH /api/v1/tramos-fidelidad` restringido a `TenantAdmin`, validando cobertura y registrando auditoría
- [ ] 3.2 `GET /api/v1/clientes/{id}/fidelidad`: conteo, tramo actual, tipo de comisión y cuántos faltan para el siguiente
- [ ] 3.3 `POST /api/v1/actas`: resolver el tramo y congelar `tipo_comision_id` + conteo en el acta
- [ ] 3.4 Rechazar `tipo_comision_id` enviado por `Sales` con `403`; aceptarlo de `Management`/`TenantAdmin` solo con motivo, marcando `OVERRIDE` y auditando
- [ ] 3.5 Exponer en `ActaDetailOut` el tipo de comisión, su origen y el conteo al firmar

## 4. Backoffice

- [ ] 4.1 Reemplazar en `/actas/nueva` el selector de tipo de comisión por la tasa resuelta con su justificación
- [ ] 4.2 Consultar la fidelidad del cliente al identificarlo por RUT y mostrar el tramo alcanzado
- [ ] 4.3 Control de override visible solo para `Management`/`TenantAdmin`, con campo de motivo obligatorio
- [ ] 4.4 `/config/fidelidad`: administración de tramos para `TenantAdmin` (la entrada de menú `cfg_fidelidad` ya existe en el seed)
- [ ] 4.5 Ficha de cliente con historial de operaciones y tramo vigente

## 5. Pruebas

- [ ] 5.1 Umbrales: 0, 1 y 2 vehículos vendidos resuelven el tramo correcto
- [ ] 5.2 Actas activas y cerradas sin venta no suman al conteo
- [ ] 5.3 El acta vigente conserva su tasa cuando el cliente sube de tramo
- [ ] 5.4 Cambiar la configuración de tramos no altera actas ya firmadas
- [ ] 5.5 `Sales` enviando `tipo_comision_id` recibe `403`; `Management` sin motivo recibe `400`
- [ ] 5.6 Tramos solapados o con huecos rechazados con `400`
- [ ] 5.7 Aislamiento entre tenants en conteo, tramos y ficha de fidelidad
- [ ] 5.8 El PDF del acta imprime la tasa congelada, no la recalculada
