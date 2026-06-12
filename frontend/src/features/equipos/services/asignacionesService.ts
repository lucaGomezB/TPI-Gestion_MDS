import api from '@/shared/services/api';
import type {
  Asignacion,
  AsignacionDisplay,
  AsignacionFilters,
  CreateAsignacionData,
  UpdateAsignacionData,
  AsignacionMasivaData,
  CloneEquipoData,
  VigenciaBulkData,
  ExportEquipoData,
  MisEquiposItem,
} from '../types/asignaciones';

// --- Individual ---

export async function getAsignaciones(filters?: AsignacionFilters): Promise<AsignacionDisplay[]> {
  const response = await api.get<AsignacionDisplay[]>('/admin/asignaciones', { params: filters });
  return response.data;
}

export async function getAsignacion(id: string): Promise<Asignacion> {
  const response = await api.get<Asignacion>(`/admin/asignaciones/${id}`);
  return response.data;
}

export async function createAsignacion(data: CreateAsignacionData): Promise<Asignacion> {
  const response = await api.post<Asignacion>('/admin/asignaciones', data);
  return response.data;
}

export async function updateAsignacion(id: string, data: UpdateAsignacionData): Promise<Asignacion> {
  const response = await api.put<Asignacion>(`/admin/asignaciones/${id}`, data);
  return response.data;
}

// --- Masiva ---

export async function createAsignacionMasiva(data: AsignacionMasivaData): Promise<{ count: number }> {
  const response = await api.post<{ count: number }>('/admin/asignaciones/masiva', data);
  return response.data;
}

// --- Clone ---

export async function cloneEquipo(data: CloneEquipoData): Promise<{ count: number }> {
  const response = await api.post<{ count: number }>('/admin/asignaciones/clonar', data);
  return response.data;
}

// --- Vigencia ---

export async function updateVigenciaBulk(data: VigenciaBulkData): Promise<{ count: number }> {
  const response = await api.put<{ count: number }>('/admin/asignaciones/vigencia', data);
  return response.data;
}

// --- Export ---

export async function exportEquipo(params: ExportEquipoData): Promise<Blob> {
  const response = await api.get('/admin/equipos/export', {
    params,
    responseType: 'blob',
  });
  return response.data;
}

// --- Mis Equipos ---

export async function getMisEquipos(): Promise<MisEquiposItem[]> {
  const response = await api.get<MisEquiposItem[]>('/mis-equipos');
  return response.data;
}
