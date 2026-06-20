export interface TareaResponse {
  id: string;
  tenant_id: string;
  materia_id: string | null;
  asignado_a: string;
  asignado_por: string;
  estado: string;
  descripcion: string;
  contexto_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TareaAdminResponse extends TareaResponse {
  comentario_count: number;
}

export interface TareaCreatePayload {
  materia_id?: string;
  asignado_a: string;
  descripcion: string;
  contexto_id?: string;
}

export interface TareaEstadoUpdatePayload {
  estado: string;
}

export interface ComentarioResponse {
  id: string;
  tenant_id: string;
  tarea_id: string;
  autor_id: string;
  texto: string;
  created_at: string;
}

export interface ComentarioCreatePayload {
  texto: string;
}

export const ESTADOS_TAREA = [
  'Pendiente',
  'En progreso',
  'Resuelta',
  'Cancelada',
] as const;

export type EstadoTarea = (typeof ESTADOS_TAREA)[number];

export const ESTADO_VARIANT_MAP: Record<string, 'warning' | 'info' | 'success' | 'error'> = {
  Pendiente: 'warning',
  'En progreso': 'info',
  Resuelta: 'success',
  Cancelada: 'error',
};

export function getNextEstados(current: string): string[] {
  switch (current) {
    case 'Pendiente':
      return ['En progreso', 'Cancelada'];
    case 'En progreso':
      return ['Resuelta', 'Cancelada'];
    case 'Resuelta':
      return ['Cancelada'];
    case 'Cancelada':
      return [];
    default:
      return [];
  }
}
