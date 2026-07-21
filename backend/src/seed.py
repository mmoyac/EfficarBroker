"""Seed de datos de desarrollo (idempotente).

Puebla catálogos (roles, ciudades, estados_vehiculo, menú por rol), la maestra
tenant `vendemostuautomovil.com` con sus sucursales, y los usuarios del equipo.
Ejecutar dentro del contenedor backend:  python -m src.seed
"""

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.config import settings
from src.database import SessionLocal
from src.models.acta import ActaChecklist, ActaEstadoHistorial, ActaRecepcion
from src.models.catalogs import (
    Ciudad,
    Color,
    Combustible,
    Comuna,
    EstadoAbono,
    EstadoChecklist,
    EstadoVehiculo,
    MenuItem,
    MenuSeccion,
    MotivoCierreActa,
    Role,
    TipoChecklistItem,
    TipoComision,
    TipoVehiculo,
    VehiculoMarca,
    VehiculoModelo,
    VehiculoVersion,
)
from src.models.cliente import Cliente
from src.models.sucursal import Sucursal
from src.models.tenant import Tenant
from src.models.user import User
from src.models.vehiculo import ChecklistItem, Vehiculo
from src.utils.security import hash_password

# ---------------------------------------------------------------------------
# Definiciones de dominio (se persisten como catálogos; NO se hardcodean en app)
# ---------------------------------------------------------------------------

# Roles reflejando los cargos reales de vendemostuautomovil.com/nosotros
# (roles es una maestra administrable por el SuperAdmin; esto es solo el estado inicial).
ROLES = [
    ("SuperAdmin", "Super Administrador", "Dueño global de la plataforma SaaS"),
    ("TenantAdmin", "Founder & CEO", "CEO/fundador del tenant; Estado de Resultados"),
    ("Management", "Administración y Operaciones", "Validaciones, catálogo y liquidaciones"),
    ("Sales", "Ejecutivo de Ventas", "Captación, actas de recepción y visitas"),
    ("Marketing", "Marketing", "Equipo de marketing; opciones de menú a definir"),
    ("AdministrativeAssistant", "Asistente Administrativo", "Apoyo administrativo; opciones de menú a definir"),
    ("Client", "Cliente Propietario", "Acceso externo al estado de su vehículo"),
]

CIUDADES = ["Santiago", "Rancagua"]

ESTADOS_VEHICULO = [
    ("PROSPECTO", "Prospecto", 1),
    ("RECEPCIONADO", "Recepcionado", 2),
    ("CONTRATO_ACEPTADO", "Contrato Aceptado", 3),
    ("PUBLICADO", "Publicado", 4),
    ("VENDIDO", "Vendido", 5),
]

# Menú del backoffice (SEMILLA_OPENSPEC Módulo 7). Estructura:
# (seccion_code, label, icon, orden, [ (item_code, label, icon, ruta, orden, [roles] ) ])
MENU = [
    ("veh_gestion", "Gestión de Vehículos", "car", 10, [
        ("veh_tasacion", "Tasación Rápida", "calculator", "/tasacion", 10, ["Sales"]),
        ("veh_actas", "Actas de Recepción", "clipboard-list", "/actas", 20, ["Sales"]),
        ("veh_captaciones", "Mis Captaciones", "list", "/captaciones", 30, ["Sales"]),
        ("veh_derivadas", "Ventas Derivadas a mi Sucursal", "arrow-left-right", "/captaciones/derivadas", 40, ["Sales"]),
    ]),
    ("agenda_visitas", "Agenda de Visitas", "calendar", 20, [
        ("agenda_calendario", "Calendario de Muestras", "calendar-days", "/agenda", 10, ["Sales"]),
        ("agenda_solicitud", "Crear Solicitud de Visita", "plus-circle", "/agenda/nueva", 20, ["Sales"]),
    ]),
    ("mis_comisiones", "Mis Comisiones", "wallet", 30, [
        ("com_historial", "Historial de Incentivos", "history", "/comisiones", 10, ["Sales"]),
    ]),
    ("control_valid", "Control y Validaciones", "shield-check", 40, [
        ("val_pendientes", "Pendientes de Aprobación", "inbox", "/validaciones/pendientes", 10, ["Management"]),
        ("val_catalogo", "Gestor del Catálogo", "layout-grid", "/catalogo", 20, ["Management"]),
        ("val_vehiculos", "Vehículos", "car", "/vehiculos", 30, ["Management"]),
    ]),
    ("ops_sucursales", "Operaciones Sucursales", "building", 50, [
        ("ops_visitas", "Monitoreo de Visitas", "eye", "/operaciones/visitas", 10, ["Management"]),
        ("ops_custodia", "Control de Custodia", "warehouse", "/operaciones/custodia", 20, ["Management"]),
    ]),
    ("liquidaciones", "Módulo de Liquidaciones", "banknote", 60, [
        ("liq_ordenes", "Órdenes de Pago", "receipt", "/liquidaciones/ordenes", 10, ["Management"]),
        ("liq_retenciones", "Retenciones por Prenda/Multas", "lock", "/liquidaciones/retenciones", 20, ["Management"]),
    ]),
    ("bi", "Business Intelligence", "bar-chart", 70, [
        ("bi_resultados", "Estado de Resultados", "trending-up", "/bi/resultados", 10, ["TenantAdmin"]),
        ("bi_performance", "Performance de Equipo", "users", "/bi/performance", 20, ["TenantAdmin"]),
    ]),
    ("config_negocio", "Configuración del Negocio", "settings", 80, [
        ("cfg_comision", "Parámetros de Comisión", "percent", "/config/comisiones", 10, ["TenantAdmin"]),
        ("cfg_fidelidad", "Reglas de Fidelidad", "star", "/config/fidelidad", 20, ["TenantAdmin"]),
        ("cfg_usuarios", "Gestión de Usuarios", "user-cog", "/config/usuarios", 30, ["TenantAdmin"]),
    ]),
    ("panel_inquilinos", "Panel de Inquilinos", "globe", 90, [
        ("saas_directorio", "Directorio de Clientes", "book-user", "/saas/tenants", 10, ["SuperAdmin"]),
        ("saas_metricas", "Métricas de Consumo", "activity", "/saas/metricas", 20, ["SuperAdmin"]),
        ("saas_facturacion", "Facturación SaaS", "credit-card", "/saas/facturacion", 30, ["SuperAdmin"]),
        ("saas_catalogo_vehicular", "Catálogo Vehicular", "list", "/saas/catalogo-vehicular", 40, ["SuperAdmin"]),
    ]),
]

# Checklist de 12 puntos del acta REAL de vendemostuautomovil.com (catálogo).
# Catálogos que reemplazan enums antes hardcodeados como texto libre.
TIPOS_CHECKLIST_ITEM = [("DOCUMENTO", "Documento"), ("ACCESORIO", "Accesorio")]
ESTADOS_CHECKLIST = [("OK", "OK"), ("FALTANTE", "Faltante"), ("OBSERVADO", "Observado")]
ESTADOS_ABONO = [
    ("NO_DEVENGADO", "Cobrado, no devengado"),
    ("APLICADO_COMISION", "Aplicado a la comisión"),
    ("RETENIDO", "Retenido por gestión"),
]
MOTIVOS_CIERRE_ACTA = [
    ("DESISTIMIENTO", "El dueño desiste de vender"),
    ("VENTA_EXTERNA", "Vendido por fuera del corredor"),
]
COLORES = [
    ("BLANCO", "Blanco"), ("NEGRO", "Negro"), ("GRIS", "Gris"), ("PLATA", "Plata"),
    ("ROJO", "Rojo"), ("AZUL", "Azul"), ("VERDE", "Verde"), ("CAFE", "Café"),
]

# (code, nombre, tipo_code, requiere_vencimiento, orden)
CHECKLIST_ITEMS = [
    ("permiso_circulacion", "Permiso de Circulación", "DOCUMENTO", True, 1),
    ("seguro_obligatorio", "Seguro Obligatorio", "DOCUMENTO", True, 2),
    ("revision_tecnica", "Revisión Técnica", "DOCUMENTO", True, 3),
    ("copia_llave", "Copia de Llave", "ACCESORIO", False, 4),
    ("manual_usuario", "Manual de Usuario", "DOCUMENTO", False, 5),
    ("dispositivo_tag", "Dispositivo TAG", "ACCESORIO", False, 6),
    ("rueda_repuesto", "Rueda de Repuesto", "ACCESORIO", False, 7),
    ("gata", "Gata", "ACCESORIO", False, 8),
    ("herramienta", "Herramienta", "ACCESORIO", False, 9),
    ("kit_seguridad", "Kit de Seguridad", "ACCESORIO", False, 10),
    ("panel_desmontable", "Panel desmontable", "ACCESORIO", False, 11),
    ("pisos_goma", "Pisos de goma", "ACCESORIO", False, 12),
]

# Catálogos del acta corporativa
COMUNAS = ["Padre Hurtado", "Santiago", "Las Condes", "Rancagua", "Providencia", "Maipú", "Puente Alto"]

TIPOS_VEHICULO = [
    ("automovil", "Automóvil"),
    ("suv", "SUV"),
    ("camioneta", "Camioneta"),
    ("station_wagon", "Station Wagon"),
    ("furgon", "Furgón"),
]

COMBUSTIBLES = [
    ("bencina", "Bencina"),
    ("diesel", "Diésel"),
    ("hibrido", "Híbrido"),
    ("electrico", "Eléctrico"),
    ("gas", "Gas"),
]

# (code, nombre, tasa, minimo) — comisión = MAX(precio*tasa, minimo)
TIPOS_COMISION = [
    ("estandar", "Estándar", 0.05, 440000),
    ("gold", "Gold", 0.03, 440000),
]

VEHICLE_CATALOG = {
    "Toyota": {
        "Yaris": ["GLI", "XLI", "Sport"],
        "Corolla": ["XEI", "SE-G", "Hybrid"],
        "RAV4": ["LE", "XLE", "Limited"],
    },
    "Hyundai": {
        "Accent": ["GL", "GLS", "Prime"],
        "Elantra": ["GL", "Limited", "N Line"],
        "Tucson": ["GL", "GLS", "Limited"],
    },
    "Kia": {
        "Rio": ["EX", "LX", "5"],
        "Cerato": ["EX", "GT Line", "SX"],
        "Sportage": ["LX", "EX", "GT Line"],
    },
    "Mazda": {
        "Mazda 2": ["V", "R", "GT"],
        "Mazda 3": ["V", "R", "GT"],
        "CX-5": ["R", "GT", "Signature"],
    },
    "Chevrolet": {
        "Spark": ["LT", "GT", "Activ"],
        "Onix": ["LT", "Premier", "RS"],
        "Tracker": ["LT", "Premier", "RS"],
    },
    "Nissan": {
        "Versa": ["Sense", "Advance", "Exclusive"],
        "Sentra": ["Sense", "Advance", "SR"],
        "Qashqai": ["Sense", "Advance", "Exclusive"],
    },
}

TENANT_DOMINIO = "vendemostuautomovil.com"
TENANT_NOMBRE = "Vendemos Tu Automóvil"
# Datos corporativos para el encabezado/firma del documento (del acta real).
TENANT_CORP = {
    "razon_social": "Vendemos tu Automóvil SPA",
    "rut": "77.141.304-8",
    "giro": "Compraventa de Automóviles",
    "telefono": "987035145",
    "web": "www.vendemostuautomovil.com",
    "logo": None,  # sin asset por ahora; el encabezado reserva el espacio
}

SUCURSALES = [
    ("Sucursal Santiago", "Los Militares 5620, Las Condes", "Santiago"),
    ("Sucursal Rancagua", "Mall Plaza América, Of. 1213", "Rancagua"),
]

# (nombre, email, telefono, role_code, tenant?, sucursal_nombre?)
SUPERADMIN_USER = ("Marcelo Moya", "mmoyainfo@gmail.com", None, "SuperAdmin")

# Segundo tenant de demostración (para probar el cambio de contexto del SuperAdmin)
DEMO_TENANT_DOMINIO = "demo.efficarbroker.com"
DEMO_TENANT_NOMBRE = "Automotora Demo"
DEMO_SUCURSAL = ("Sucursal Demo Centro", "Av. Demo 100", "Santiago")
DEMO_USER = ("Admin Demo", "admin@demo.efficarbroker.com", None, "TenantAdmin")

# (nombre, email, telefono, role_code, sucursal_nombre, rut)
TENANT_USERS = [
    ("Bastian Galve", "bastian@vendemostuautomovil.com", None, "TenantAdmin", None, None),
    ("Josefa Cuevas", "josefa@vendemostuautomovil.com", "964015403", "Management", None, None),
    ("Araneth Díaz", "araneth@vendemostuautomovil.com", "950430735", "Sales", "Sucursal Santiago", "26.441.328-1"),
    ("Juan Guillermo Rojas", "juanguillermo@vendemostuautomovil.com", "932334519", "Sales", "Sucursal Santiago", "18.234.567-8"),
    ("Cristian Farías", "cristian@vendemostuautomovil.com", "957013066", "Sales", "Sucursal Rancagua", "17.345.678-9"),
    ("Gabriel Hernández", "gabriel@vendemostuautomovil.com", "983463621", "Sales", "Sucursal Rancagua", "19.456.789-0"),
    ("Alejandro Debezzi", "alejandro@vendemostuautomovil.com", "956300358", "Marketing", "Sucursal Santiago", None),
    ("Matteo Galve", "matteo@vendemostuautomovil.com", "930775979", "AdministrativeAssistant", "Sucursal Santiago", None),
]


def _get_or_create(db: Session, model, defaults: dict | None = None, **filters):
    instance = db.scalar(select(model).filter_by(**filters))
    if instance is not None:
        return instance, False
    params = {**filters, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def _crear_acta_seed(
    db: Session, *, tenant_id: int, vehiculo, cliente, captador,
    sucursal_origen, sucursal_venta, estado, estado_abono, tipo_comision,
    km: int, precio: int, cerrada: bool,
    vendedor=None, precio_final: int | None = None,
) -> ActaRecepcion:
    """Crea un acta de seed con su registro de historial de estado."""
    acta = ActaRecepcion(
        tenant_id=tenant_id, vehiculo_id=vehiculo.id, cliente_id=cliente.id,
        captador_user_id=captador.id, sucursal_id=sucursal_origen.id,
        sucursal_venta_id=sucursal_venta.id, estado_id=estado.id,
        km_ingreso=km, fecha_recepcion=date.today(),
        precio_venta_pactado=precio, vigencia_dias=30, tipo_comision_id=tipo_comision.id,
        exclusividad_abono=40000, estado_abono_id=estado_abono.id,
        fecha_cobro_abono=date.today(),
        vendedor_user_id=vendedor.id if vendedor else None,
        precio_venta_final=precio_final,
        fecha_venta=date.today() if cerrada and vendedor else None,
        cerrada=cerrada, fecha_cierre=date.today() if cerrada else None,
    )
    db.add(acta)
    db.flush()
    db.add(ActaEstadoHistorial(
        tenant_id=tenant_id, acta_id=acta.id, estado_id=estado.id, user_id=captador.id,
    ))
    db.flush()
    return acta


def seed() -> None:
    db = SessionLocal()
    try:
        # --- Catálogo: roles ---
        roles: dict[str, Role] = {}
        for code, nombre, desc in ROLES:
            role, _ = _get_or_create(db, Role, defaults={"nombre": nombre, "descripcion": desc}, code=code)
            roles[code] = role

        # --- Catálogo: ciudades ---
        ciudades: dict[str, Ciudad] = {}
        for nombre in CIUDADES:
            ciudad, _ = _get_or_create(db, Ciudad, nombre=nombre)
            ciudades[nombre] = ciudad

        # --- Catálogo: estados de vehículo ---
        for code, nombre, orden in ESTADOS_VEHICULO:
            _get_or_create(db, EstadoVehiculo, defaults={"nombre": nombre, "orden": orden}, code=code)

        # --- Catálogo: marcas/modelos/versiones de vehículos ---
        for marca_nombre, modelos in VEHICLE_CATALOG.items():
            marca, _ = _get_or_create(db, VehiculoMarca, nombre=marca_nombre)
            for modelo_nombre, versiones in modelos.items():
                modelo, _ = _get_or_create(
                    db,
                    VehiculoModelo,
                    marca_id=marca.id,
                    nombre=modelo_nombre,
                )
                for version_nombre in versiones:
                    _get_or_create(
                        db,
                        VehiculoVersion,
                        modelo_id=modelo.id,
                        nombre=version_nombre,
                    )

        # --- Catálogos que reemplazan enums antes hardcodeados ---
        tipos_checklist: dict[str, TipoChecklistItem] = {}
        for code, nombre in TIPOS_CHECKLIST_ITEM:
            t, _ = _get_or_create(db, TipoChecklistItem, defaults={"nombre": nombre}, code=code)
            tipos_checklist[code] = t
        for code, nombre in ESTADOS_CHECKLIST:
            _get_or_create(db, EstadoChecklist, defaults={"nombre": nombre}, code=code)
        estados_abono: dict[str, EstadoAbono] = {}
        for code, nombre in ESTADOS_ABONO:
            ea, _ = _get_or_create(db, EstadoAbono, defaults={"nombre": nombre}, code=code)
            estados_abono[code] = ea
        for code, nombre in MOTIVOS_CIERRE_ACTA:
            _get_or_create(db, MotivoCierreActa, defaults={"nombre": nombre}, code=code)
        colores: dict[str, Color] = {}
        for code, nombre in COLORES:
            col, _ = _get_or_create(db, Color, defaults={"nombre": nombre}, code=code)
            colores[code] = col

        # --- Catálogo: checklist de 12 puntos (AUTORITATIVO: refleja el acta real) ---
        for code, nombre, tipo_code, req_venc, orden in CHECKLIST_ITEMS:
            tipo_id = tipos_checklist[tipo_code].id
            item, _ = _get_or_create(
                db, ChecklistItem,
                defaults={"nombre": nombre, "tipo_id": tipo_id, "requiere_vencimiento": req_venc, "orden": orden},
                code=code,
            )
            item.nombre, item.tipo_id, item.requiere_vencimiento, item.orden = nombre, tipo_id, req_venc, orden
        # Purga de ítems antiguos que ya no están en el acta real (dev): borra sus
        # marcas en acta_checklist y luego el ítem.
        real_codes = {code for code, *_ in CHECKLIST_ITEMS}
        for stale in db.scalars(select(ChecklistItem).where(ChecklistItem.code.not_in(real_codes))).all():
            db.execute(delete(ActaChecklist).where(ActaChecklist.checklist_item_id == stale.id))
            db.delete(stale)
        db.flush()

        # --- Catálogos del acta corporativa ---
        comunas: dict[str, Comuna] = {}
        for nombre in COMUNAS:
            com, _ = _get_or_create(db, Comuna, nombre=nombre)
            comunas[nombre] = com
        for code, nombre in TIPOS_VEHICULO:
            _get_or_create(db, TipoVehiculo, defaults={"nombre": nombre}, code=code)
        for code, nombre in COMBUSTIBLES:
            _get_or_create(db, Combustible, defaults={"nombre": nombre}, code=code)
        tipos_comision: dict[str, TipoComision] = {}
        for code, nombre, tasa, minimo in TIPOS_COMISION:
            tc, _ = _get_or_create(
                db, TipoComision,
                defaults={"nombre": nombre, "tasa": tasa, "minimo": minimo},
                code=code,
            )
            tipos_comision[code] = tc

        # --- Catálogo: menú (secciones + items + mapeo por rol) ---
        for sec_code, sec_label, sec_icon, sec_orden, items in MENU:
            seccion, _ = _get_or_create(
                db, MenuSeccion,
                defaults={"label": sec_label, "icon": sec_icon, "orden": sec_orden},
                code=sec_code,
            )
            for item_code, label, icon, ruta, orden, role_codes in items:
                item, _ = _get_or_create(
                    db, MenuItem,
                    defaults={"label": label, "icon": icon, "ruta": ruta, "orden": orden, "seccion_id": seccion.id},
                    code=item_code,
                )
                # Mapeo rol -> item (idempotente)
                existing = {r.code for r in item.roles}
                for rc in role_codes:
                    if rc not in existing and rc in roles:
                        item.roles.append(roles[rc])

        # --- Maestra: tenant (con datos corporativos para el documento) ---
        tenant, _ = _get_or_create(
            db, Tenant, defaults={"nombre": TENANT_NOMBRE, "activo": True}, dominio=TENANT_DOMINIO
        )
        tenant.razon_social = TENANT_CORP["razon_social"]
        tenant.rut = TENANT_CORP["rut"]
        tenant.giro = TENANT_CORP["giro"]
        tenant.telefono = TENANT_CORP["telefono"]
        tenant.web = TENANT_CORP["web"]
        tenant.logo = TENANT_CORP["logo"]

        # --- Maestra: sucursales ---
        sucursales: dict[str, Sucursal] = {}
        for nombre, direccion, ciudad_nombre in SUCURSALES:
            suc, _ = _get_or_create(
                db, Sucursal,
                defaults={"direccion": direccion, "ciudad_id": ciudades[ciudad_nombre].id},
                tenant_id=tenant.id, nombre=nombre,
            )
            sucursales[nombre] = suc

        pwd = hash_password(settings.SEED_DEFAULT_PASSWORD)

        # --- Usuario SuperAdmin (plataforma, sin tenant) ---
        nombre, email, tel, role_code = SUPERADMIN_USER
        _get_or_create(
            db, User,
            defaults={
                "nombre": nombre, "telefono": tel, "role_id": roles[role_code].id,
                "tenant_id": None, "sucursal_id": None, "password_hash": pwd, "activo": True,
            },
            email=email,
        )

        # --- Usuarios del tenant ---
        for nombre, email, tel, role_code, suc_nombre, rut in TENANT_USERS:
            suc_id = sucursales[suc_nombre].id if suc_nombre else None
            user, _ = _get_or_create(
                db, User,
                defaults={
                    "nombre": nombre, "telefono": tel, "role_id": roles[role_code].id,
                    "tenant_id": tenant.id, "sucursal_id": suc_id,
                    "password_hash": pwd, "activo": True,
                },
                email=email,
            )
            user.rut = rut

        # --- Operacional demo: vehículo DERIVADO (captado en Rancagua, venta en Santiago) ---
        # Valida el flujo de derivación end-to-end: sucursal_id != sucursal_venta_id.
        captador = db.scalar(
            select(User).where(User.email == "cristian@vendemostuautomovil.com")
        )
        version_demo = db.scalar(
            select(VehiculoVersion).join(VehiculoModelo).join(VehiculoMarca)
            .where(VehiculoMarca.nombre == "Toyota", VehiculoModelo.nombre == "Corolla", VehiculoVersion.nombre == "XEI")
        )
        estado_recep = db.scalar(select(EstadoVehiculo).where(EstadoVehiculo.code == "RECEPCIONADO"))
        estado_vendido = db.scalar(select(EstadoVehiculo).where(EstadoVehiculo.code == "VENDIDO"))
        if captador and version_demo and estado_recep:
            cliente_demo, _ = _get_or_create(
                db, Cliente,
                defaults={
                    "nombre": "Cliente Derivado Demo", "email": None, "telefono": None,
                    "domicilio": "Av. Ejemplo 1234", "comuna_id": comunas["Santiago"].id,
                },
                tenant_id=tenant.id, rut="11111111-1",
            )
            cliente_demo.domicilio = "Av. Ejemplo 1234"
            cliente_demo.comuna_id = comunas["Santiago"].id
            veh_demo, _ = _get_or_create(
                db, Vehiculo,
                defaults={
                    "version_id": version_demo.id, "anio": 2019,
                    "n_motor": None, "n_chasis": None, "color_id": colores["GRIS"].id,
                },
                tenant_id=tenant.id, ppu="DERV01",
            )
            veh_demo.color_id = veh_demo.color_id or colores["GRIS"].id
            db.flush()
            # Acta ACTIVA (derivada) sobre ese vehículo, si no tiene ninguna.
            tiene_acta = db.scalar(
                select(ActaRecepcion.id).where(ActaRecepcion.vehiculo_id == veh_demo.id)
            )
            if not tiene_acta:
                _crear_acta_seed(
                    db, tenant_id=tenant.id, vehiculo=veh_demo, cliente=cliente_demo,
                    captador=captador, sucursal_origen=sucursales["Sucursal Rancagua"],
                    sucursal_venta=sucursales["Sucursal Santiago"],
                    estado=estado_recep, estado_abono=estados_abono["NO_DEVENGADO"],
                    tipo_comision=tipos_comision["estandar"], km=45000,
                    precio=12000000, cerrada=False,
                )

        # --- Operacional demo: REINGRESO (mismo auto, dos dueños) ---
        # Un vehículo con un acta ya VENDIDA y otra activa: cubre el caso que el
        # modelo viejo hacía imposible.
        cap_stgo = db.scalar(select(User).where(User.email == "araneth@vendemostuautomovil.com"))
        version_ri = db.scalar(
            select(VehiculoVersion).join(VehiculoModelo).join(VehiculoMarca)
            .where(VehiculoModelo.nombre == "Corolla")
        )
        if cap_stgo and version_ri and estado_recep and estado_vendido:
            veh_ri, nuevo = _get_or_create(
                db, Vehiculo,
                defaults={"version_id": version_ri.id, "anio": 2017, "color_id": colores["NEGRO"].id},
                tenant_id=tenant.id, ppu="REING01",
            )
            if nuevo or not db.scalar(select(ActaRecepcion.id).where(ActaRecepcion.vehiculo_id == veh_ri.id)):
                cli_1, _ = _get_or_create(
                    db, Cliente, defaults={"nombre": "Primer Dueño Demo", "comuna_id": comunas["Santiago"].id},
                    tenant_id=tenant.id, rut="22222222-2",
                )
                cli_2, _ = _get_or_create(
                    db, Cliente, defaults={"nombre": "Segundo Dueño Demo", "comuna_id": comunas["Santiago"].id},
                    tenant_id=tenant.id, rut="33333333-3",
                )
                # Acta 1: vendida en el pasado (cerrada).
                _crear_acta_seed(
                    db, tenant_id=tenant.id, vehiculo=veh_ri, cliente=cli_1, captador=cap_stgo,
                    sucursal_origen=sucursales["Sucursal Santiago"], sucursal_venta=sucursales["Sucursal Santiago"],
                    estado=estado_vendido, estado_abono=estados_abono["APLICADO_COMISION"],
                    tipo_comision=tipos_comision["estandar"], km=60000, precio=8500000,
                    cerrada=True, vendedor=cap_stgo, precio_final=8300000,
                )
                # Acta 2: el mismo auto vuelve, otro dueño, recepción vigente.
                _crear_acta_seed(
                    db, tenant_id=tenant.id, vehiculo=veh_ri, cliente=cli_2, captador=cap_stgo,
                    sucursal_origen=sucursales["Sucursal Santiago"], sucursal_venta=sucursales["Sucursal Santiago"],
                    estado=estado_recep, estado_abono=estados_abono["NO_DEVENGADO"],
                    tipo_comision=tipos_comision["gold"], km=88000, precio=7900000, cerrada=False,
                )

        # --- 2º tenant demo (para probar cambio de contexto del SuperAdmin) ---
        demo_tenant, _ = _get_or_create(
            db, Tenant, defaults={"nombre": DEMO_TENANT_NOMBRE, "activo": True},
            dominio=DEMO_TENANT_DOMINIO,
        )
        d_nombre, d_dir, d_ciudad = DEMO_SUCURSAL
        demo_suc, _ = _get_or_create(
            db, Sucursal,
            defaults={"direccion": d_dir, "ciudad_id": ciudades[d_ciudad].id},
            tenant_id=demo_tenant.id, nombre=d_nombre,
        )
        du_nombre, du_email, du_tel, du_role = DEMO_USER
        _get_or_create(
            db, User,
            defaults={
                "nombre": du_nombre, "telefono": du_tel, "role_id": roles[du_role].id,
                "tenant_id": demo_tenant.id, "sucursal_id": demo_suc.id,
                "password_hash": pwd, "activo": True,
            },
            email=du_email,
        )

        db.commit()
        print("Seed completado: catálogos, tenants (vendemostuautomovil + demo), sucursales y usuarios listos.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
