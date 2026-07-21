export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessToken {
  access_token: string;
  token_type: string;
}

export interface UserMe {
  id: number;
  nombre: string;
  email: string;
  telefono: string | null;
  role: string;
  role_code: string;
  tenant_id: number | null;
  tenant: string | null;
  sucursal_id: number | null;
  active_tenant_id: number | null;
  active_tenant: string | null;
}

export interface Tenant {
  id: number;
  nombre: string;
  dominio: string;
  activo: boolean;
  max_usuarios: number | null;
  usuarios_activos: number;
}

export interface Role {
  id: number;
  code: string;
  nombre: string;
  descripcion: string | null;
}

export interface Sucursal {
  id: number;
  nombre: string;
  direccion: string | null;
  ciudad_id: number;
}

export interface User {
  id: number;
  nombre: string;
  email: string;
  telefono: string | null;
  role_id: number;
  role: string;
  role_code: string;
  sucursal_id: number | null;
  sucursal: string | null;
  activo: boolean;
}

export interface UserCreateInput {
  nombre: string;
  email: string;
  role_id: number;
  sucursal_id: number | null;
  telefono: string | null;
}

export type UserUpdateInput = Partial<{
  nombre: string;
  telefono: string | null;
  role_id: number;
  sucursal_id: number | null;
  activo: boolean;
}>;

/** Corrección de la ficha física del auto (mantenedor). */
export type VehiculoUpdateInput = Partial<{
  ppu: string;
  version_id: number;
  anio: number;
  n_motor: string | null;
  n_chasis: string | null;
  color_id: number | null;
  tipo_vehiculo_id: number | null;
  combustible_id: number | null;
  motivo: string | null;
}>;

/** Edición del acta mientras está en RECEPCIONADO (todo lo circunstancial). */
export type ActaUpdateInput = Partial<{
  sucursal_id: number;
  sucursal_venta_id: number;
  vendedor_user_id: number | null;
  km_ingreso: number;
  tipo_comision_id: number;
  precio_venta_pactado: number;
  vigencia_dias: number;
  exclusividad_abono: number;
  observaciones: string | null;
  cliente_nombre: string;
  cliente_email: string | null;
  cliente_telefono: string | null;
  cliente_domicilio: string | null;
  cliente_comuna_id: number | null;
  checklist: ChecklistEntryInput[];
}>;

export interface CodeNombre {
  id: number;
  code: string;
  nombre: string;
}

export interface ChecklistItem {
  id: number;
  code: string;
  nombre: string;
  tipo_id: number;
  requiere_vencimiento: boolean;
  orden: number;
}

export interface ChecklistEntryInput {
  checklist_item_id: number;
  presente: boolean;
  estado_checklist_id: number | null;
  fecha_vencimiento: string | null;
  observacion: string | null;
}

export interface ActaCreateInput {
  cliente: {
    rut: string;
    nombre: string;
    email: string | null;
    telefono: string | null;
    domicilio: string | null;
    comuna_id: number | null;
  };
  ppu: string;
  version_id: number;
  anio: number;
  n_motor: string | null;
  n_chasis: string | null;
  color_id: number | null;
  tipo_vehiculo_id: number | null;
  combustible_id: number | null;
  km_ingreso: number;
  sucursal_id: number | null;
  sucursal_venta_id: number;
  vendedor_user_id: number | null;
  tipo_comision_id: number;
  precio_venta_pactado: number;
  vigencia_dias: number;
  exclusividad_abono: number;
  observaciones: string | null;
  checklist: ChecklistEntryInput[];
}

export interface Comuna {
  id: number;
  nombre: string;
}

export interface TipoVehiculo {
  id: number;
  code: string;
  nombre: string;
}

export interface Combustible {
  id: number;
  code: string;
  nombre: string;
}

export interface TipoComision {
  id: number;
  code: string;
  nombre: string;
  tasa: number;
  minimo: number;
}

export interface ClienteLookup {
  found: boolean;
  cliente: {
    id: number;
    rut: string;
    nombre: string;
    email: string | null;
    telefono: string | null;
    domicilio: string | null;
    comuna_id: number | null;
    comuna: string | null;
  } | null;
}

export interface VehiculoGlobalLookup {
  found: boolean;
  vehiculo: {
    id: number;
    tenant_id: number;
    tenant_nombre: string;
    ppu: string;
    marca: string;
    modelo: string;
    anio: number;
    n_motor: string | null;
    n_chasis: string | null;
    estado_code: string;
  } | null;
}

export interface TasacionSimularInput {
  ppu: string;
  version_id: number;
  anio: number;
  km: number;
  referencia_url?: string | null;
}

export interface VehiculoMarcaCatalog {
  id: number;
  nombre: string;
}

export interface VehiculoModeloCatalog {
  id: number;
  marca_id: number;
  nombre: string;
}

export interface VehiculoVersionCatalog {
  id: number;
  modelo_id: number;
  nombre: string;
}

export interface TasacionSimularResult {
  prospecto_id: number;
  ppu: string;
  km: number;
  precio_mercado: number;
  precio_retoma: number;
  precio_publicacion_sugerido: number;
  fuente: string;
  observacion: string;
  sample_size: number;
  scrape_url: string | null;
}

export interface TasacionProspecto {
  id: number;
  ppu: string;
  km: number;
  precio_mercado: number;
  precio_retoma: number;
  precio_publicacion_sugerido: number;
  fuente: string;
  observacion: string | null;
  sample_size: number;
  estado_code: string;
  captador: string;
}

/** Identidad física del auto (entidad fuerte). Sin dueño ni datos de venta. */
export interface VehiculoFicha {
  id: number;
  ppu: string;
  version_id: number;
  marca_id: number;
  modelo_id: number;
  marca: string;
  modelo: string;
  version: string;
  anio: number;
  n_motor: string | null;
  n_chasis: string | null;
  color: string | null;
  color_id: number | null;
  tipo_vehiculo: string | null;
  combustible: string | null;
}

/** El acta: la unión cliente <-> vehículo en un momento dado. */
export interface Acta {
  id: number;
  vehiculo_id: number;
  vehiculo: VehiculoFicha;
  ppu: string;
  cliente: string;
  captador: string;
  vendedor: string | null;
  estado: string;
  estado_code: string;
  sucursal_id: number;
  sucursal_venta_id: number;
  sucursal: string;
  sucursal_venta: string;
  derivado: boolean;
  km_ingreso: number;
  tipo_comision: string | null;
  precio_venta_pactado: number;
  comision: number;
  liquidacion: number;
  exclusividad_abono: number;
  estado_abono: string;
  estado_abono_code: string;
  precio_venta_final: number | null;
  fecha_recepcion: string;
  fecha_venta: string | null;
  observaciones: string | null;
  cerrada: boolean;
  motivo_cierre: string | null;
  fecha_cierre: string | null;
}

export interface EquipoVenta {
  id: number;
  nombre: string;
  email: string;
  sucursal_id: number | null;
  sucursal: string | null;
}

export interface ActaChecklistRow {
  checklist_item_id: number;
  item: string;
  tipo: string;
  presente: boolean;
  estado_checklist_id: number | null;
  estado: string | null;
  fecha_vencimiento: string | null;
  observacion: string | null;
}

export interface ActaDetail extends Acta {
  vigencia_dias: number;
  comision_neta: number;
  cliente_detalle: {
    id: number;
    rut: string;
    nombre: string;
    email: string | null;
    telefono: string | null;
    domicilio: string | null;
    comuna_id: number | null;
    comuna: string | null;
  };
  checklist: ActaChecklistRow[];
}

export interface ActaHistorialItem {
  id: number;
  cliente: string;
  captador: string;
  estado_code: string;
  fecha_recepcion: string;
  fecha_venta: string | null;
  precio_venta_pactado: number;
  precio_venta_final: number | null;
  cerrada: boolean;
  motivo_cierre: string | null;
}

export interface VehiculoLookup {
  found: boolean;
  vehiculo: VehiculoFicha | null;
  tiene_acta_activa: boolean;
  total_actas: number;
}

export interface AbonoResumen {
  comprometido: number;
  ganado: number;
  detalle: { estado_code: string; estado: string; total: number; cantidad: number }[];
}

export interface MenuItem {
  code: string;
  label: string;
  icon: string | null;
  ruta: string;
}

export interface MenuSection {
  code: string;
  label: string;
  icon: string | null;
  items: MenuItem[];
}

export interface NavigationMenu {
  sections: MenuSection[];
}
