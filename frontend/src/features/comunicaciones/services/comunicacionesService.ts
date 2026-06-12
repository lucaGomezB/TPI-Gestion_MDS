import api from '@/shared/services/api';
import type {
  Comunicacion,
  ComunicacionPreviewRequest,
  ComunicacionPreviewResponse,
  ComunicacionEnviarRequest,
  AprobarComunicacionRequest,
} from '../types';

export async function getComunicaciones(materiaId?: string): Promise<Comunicacion[]> {
  const params = materiaId ? { materia_id: materiaId } : {};
  const response = await api.get<Comunicacion[]>('/materias/comunicaciones', { params });
  return response.data;
}

export async function previewComunicacion(
  materiaId: string,
  data: ComunicacionPreviewRequest,
): Promise<ComunicacionPreviewResponse> {
  const response = await api.post<ComunicacionPreviewResponse>(
    `/materias/${materiaId}/comunicaciones/preview`,
    data,
  );
  return response.data;
}

export async function enviarComunicacion(
  materiaId: string,
  data: ComunicacionEnviarRequest,
): Promise<Comunicacion> {
  const response = await api.post<Comunicacion>(
    `/materias/${materiaId}/comunicaciones/enviar`,
    data,
  );
  return response.data;
}

export async function aprobarComunicacion(
  id: string,
  data: AprobarComunicacionRequest,
): Promise<Comunicacion> {
  const response = await api.put<Comunicacion>(`/admin/comunicaciones/${id}/aprobar`, data);
  return response.data;
}

export async function cancelarComunicacion(id: string): Promise<Comunicacion> {
  const response = await api.put<Comunicacion>(`/admin/comunicaciones/${id}/cancelar`);
  return response.data;
}
