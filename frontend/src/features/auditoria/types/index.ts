export interface AuditEntry {
  id: string;
  fecha_hora: string;
  actor_id: string;
  actor_nombre?: string;
  impersonado_id?: string;
  impersonado_nombre?: string;
  materia_id?: string;
  materia_nombre?: string;
  accion: string;
  detalle?: Record<string, unknown>;
  filas_afectadas?: number;
  ip?: string;
  user_agent?: string;
}

export interface AuditSearchResponse {
  items: AuditEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditFilters {
  q?: string;
  accion?: string;
  actor_id?: string;
  materia_id?: string;
  ip?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  limit: number;
  offset: number;
}

export interface DocenteInteracciones {
  docente_id: string;
  docente_nombre?: string;
  total_acciones: number;
  por_accion: Record<string, number>;
  por_materia: Array<{ materia_id: string; nombre: string; total: number }>;
  ultimas_acciones: AuditEntry[];
}

export interface AccionesPorDia {
  fecha: string;
  total: number;
  por_accion: Record<string, number>;
}

export interface AuditDashboardData {
  acciones_por_dia: AccionesPorDia[];
  total_acciones: number;
  acciones_unicas_por_usuario: number;
  periodo_mas_activo: string;
}

export const ACCIONES_LABELS: Record<string, string> = {
  LOGIN: 'Inicio de sesión',
  LOGOUT: 'Cierre de sesión',
  USUARIO_CREAR: 'Crear usuario',
  USUARIO_MODIFICAR: 'Modificar usuario',
  USUARIO_ELIMINAR: 'Eliminar usuario',
  MATERIA_CREAR: 'Crear materia',
  MATERIA_MODIFICAR: 'Modificar materia',
  MATERIA_ELIMINAR: 'Eliminar materia',
  COMISION_CREAR: 'Crear comisión',
  COMISION_MODIFICAR: 'Modificar comisión',
  COMISION_ELIMINAR: 'Eliminar comisión',
  CALIFICACIONES_IMPORTAR: 'Importar calificaciones',
  CALIFICACIONES_MODIFICAR: 'Modificar calificaciones',
  ENCUENTRO_CREAR: 'Crear encuentro',
  ENCUENTRO_MODIFICAR: 'Modificar encuentro',
  ENCUENTRO_ELIMINAR: 'Eliminar encuentro',
  COLOQUIO_CREAR: 'Crear coloquio',
  COLOQUIO_MODIFICAR: 'Modificar coloquio',
  COLOQUIO_ELIMINAR: 'Eliminar coloquio',
  MENSAJE_ENVIAR: 'Enviar mensaje',
  AVISO_CREAR: 'Crear aviso',
  AVISO_MODIFICAR: 'Modificar aviso',
  AVISO_ELIMINAR: 'Eliminar aviso',
  EQUIPO_CREAR: 'Crear equipo',
  EQUIPO_MODIFICAR: 'Modificar equipo',
  EQUIPO_ELIMINAR: 'Eliminar equipo',
  LIQUIDACION_GENERAR: 'Generar liquidación',
  LIQUIDACION_MODIFICAR: 'Modificar liquidación',
  EXPORTAR_DATOS: 'Exportar datos',
  CONFIGURACION_MODIFICAR: 'Modificar configuración',
};

export const PAGE_SIZES = [20, 50, 100, 200] as const;

export const DEFAULT_PAGE_SIZE = 50;

export const ACCIONES_LIST = Object.keys(ACCIONES_LABELS);
