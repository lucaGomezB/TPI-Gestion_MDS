export type DiaSemana = 'Lunes' | 'Martes' | 'Miércoles' | 'Jueves' | 'Viernes' | 'Sábado' | 'Domingo';

export type EstadoEncuentro = 'Programado' | 'Realizado' | 'Cancelado';

export interface SlotEncuentro {
  id: string;
  materia_id: string;
  materia_nombre: string;
  titulo: string;
  dia_semana: DiaSemana;
  hora: string;
  fecha_inicio: string;
  cant_semanas: number;
  meet_url?: string;
  activo: boolean;
}

export interface InstanciaEncuentro {
  id: string;
  materia_id: string;
  materia_nombre: string;
  titulo: string;
  fecha: string;
  hora: string;
  estado: EstadoEncuentro;
  meet_url?: string;
  video_url?: string;
  comentario?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSlotPayload {
  materia_id: string;
  titulo: string;
  dia_semana: DiaSemana;
  hora: string;
  fecha_inicio: string;
  cant_semanas: number;
  meet_url?: string;
}

export interface CreateUnicoPayload {
  materia_id: string;
  titulo: string;
  fecha: string;
  hora: string;
  meet_url?: string;
}

export interface UpdateEncuentroPayload {
  estado?: EstadoEncuentro;
  meet_url?: string;
  video_url?: string;
  comentario?: string;
}

export interface EmbedSnippetResponse {
  snippet: string;
  formato: 'html' | 'markdown';
}

export interface AdminEncuentrosQueryParams {
  materia_id?: string;
  estado?: EstadoEncuentro;
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
