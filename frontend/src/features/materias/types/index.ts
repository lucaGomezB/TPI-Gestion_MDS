export interface Materia {
  id: string;
  nombre: string;
  cohorte: string;
  comisiones: string[];
  tenant_id: string;
}

export interface Calificacion {
  id: string;
  alumno_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  comision: string;
  actividad: string;
  nota: number;
  fecha: string;
  tipo: string;
}

export interface UmbralMateria {
  umbral_pct: number;
  materia_id: string;
}

export interface Atrasado {
  id: string;
  alumno_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  comision: string;
  razon: 'faltante' | 'nota_baja';
  nota_minima?: number;
  umbral: number;
}

export interface RankingItem {
  alumno_id: string;
  nombre: string;
  apellidos: string;
  comision: string;
  actividades_aprobadas: number;
  total_actividades: number;
  porcentaje: number;
}

export interface Reporte {
  total_alumnos: number;
  total_actividades: number;
  promedio_general: number;
  aprobados: number;
  reprobados: number;
  atrasados: number;
}

export interface NotaFinal {
  alumno_id: string;
  nombre: string;
  apellidos: string;
  comision: string;
  total_actividades: number;
  nota_final: number;
  estado: 'aprobado' | 'reprobado';
}

export interface SeguimientoItem {
  alumno_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  comision: string;
  total_actividades: number;
  total_aprobadas: number;
  total_pendientes: number;
  ultima_actividad?: string;
}

export interface ImportPreview {
  actividades: ImportActivity[];
  total_filas: number;
}

export interface ImportActivity {
  actividad: string;
  filas: number;
  seleccionada: boolean;
}

export interface AtrasadosFilters {
  comision?: string;
  busqueda?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface SeguimientoFilters {
  busqueda?: string;
  comision?: string;
  actividad?: string;
  regional?: string;
  minimo_actividades?: number;
}

export interface MateriaKPI {
  materia: Materia;
  atrasados_count: number;
  pendientes_count: number;
  proximo_examen?: string;
  error?: string;
}

// === Task 1.1: Padron types ===
export interface PadronAlumno {
  alumno_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  comision: string;
}

export interface PadronImportResult {
  total_filas: number;
  importadas: number;
  duplicadas: number;
  errores: string[];
}

// === Task 1.2: CompletionReport types ===
export interface CompletionReportItem {
  alumno_id: string;
  nombre: string;
  apellidos: string;
  email: string;
  actividad: string;
  estado: 'completado' | 'pendiente';
  fecha_entrega?: string;
}

export interface CompletionReportResult {
  materia_id: string;
  total_alumnos: number;
  total_pendientes: number;
  total_completados: number;
  items: CompletionReportItem[];
}

// === Task 1.3: MonitorGeneral types ===
export interface MonitorGeneralItem {
  materia_id: string;
  materia_nombre: string;
  cohorte: string;
  comision: string;
  total_alumnos: number;
  total_actividades: number;
  promedio_general: number;
  aprobados: number;
  reprobados: number;
  atrasados_count: number;
  pendientes_count: number;
}

export interface MonitorGeneralFilters {
  materia_id?: string;
  regional?: string;
  comision?: string;
  busqueda?: string;
  status?: 'todos' | 'con_atrasados' | 'sin_datos';
}
