export type EstadoGuardia = 'Pendiente' | 'Paga' | 'Anulada';

export type DiaSemana = 'Lunes' | 'Martes' | 'Miércoles' | 'Jueves' | 'Viernes' | 'Sábado' | 'Domingo';

export interface Guardia {
  id: string;
  materia_id: string;
  materia_nombre: string;
  asignacion_id: string;
  carrera_id: string;
  cohorte_id: string;
  dia: DiaSemana;
  horario: string;
  estado: EstadoGuardia;
  comentarios?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateGuardiaPayload {
  asignacion_id: string;
  carrera_id: string;
  cohorte_id: string;
  dia: DiaSemana;
  horario: string;
  comentarios?: string;
}

export interface GuardiaFilters {
  estado?: EstadoGuardia;
  fecha_desde?: string;
  fecha_hasta?: string;
  page?: number;
  per_page?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
