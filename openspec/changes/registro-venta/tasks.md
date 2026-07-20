## 1. Backend

- [x] 1.1 Añadir `vendedor_user_id`, `precio_venta_final`, `fecha_venta` al modelo `Vehiculo` + migración 0005
- [x] 1.2 `GET /api/v1/equipo-ventas` (usuarios Sales activos del tenant; roles Sales/Management/TenantAdmin)
- [x] 1.3 `POST /api/v1/vehiculos/{id}/registrar-venta` (valida vendedor Sales activo, estado CONTRATO_ACEPTADO/PUBLICADO, setea venta, → VENDIDO, historial + auditoría; 409/400 en inválidos)
- [x] 1.4 Exponer captador y vendedor en `VehiculoOut`/detalle
- [x] 1.5 `GET /sucursales` accesible a Sales

## 2. Backoffice

- [x] 2.1 Tipos/servicios: equipo-ventas, registrar-venta; campos vendedor en Vehiculo
- [x] 2.2 "Mis Captaciones": acción "Registrar venta" (modal: vendedor + precio final) para autos elegibles; columnas captador/vendedor

## 3. Verificación

- [x] 3.1 Flujo Araneth capta → aceptar términos → registrar venta con Cristian → VENDIDO con captador Araneth y vendedor Cristian
- [x] 3.2 Reglas: transición inválida 409; vendedor inválido 400 (Josefa/Management); historial con VENDIDO; sucursales visibles a Sales
