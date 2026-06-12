import api from '@/shared/services/api';
import type {
  InstanciaEncuentro,
  CreateSlotPayload,
  CreateUnicoPayload,
  UpdateEncuentroPayload,
  EmbedSnippetResponse,
  AdminEncuentrosQueryParams,
  PaginatedResponse,
} from '../types/encuentroTypes';

export async function getEncuentrosAdmin(
  params: Partial<AdminEncuentrosQueryParams>,
): Promise<PaginatedResponse<InstanciaEncuentro>> {
  const response = await api.get<PaginatedResponse<InstanciaEncuentro>>('/admin/encuentros', { params });
  return response.data;
}

export async function createSlot(payload: CreateSlotPayload): Promise<{ id: string }> {
  const { materia_id, ...data } = payload;
  const response = await api.post<{ id: string }>(`/materias/${materia_id}/encuentros/slot`, data);
  return response.data;
}

export async function createUnico(payload: CreateUnicoPayload): Promise<{ id: string }> {
  const { materia_id, ...data } = payload;
  const response = await api.post<{ id: string }>(`/materias/${materia_id}/encuentros/unico`, data);
  return response.data;
}

export async function updateEncuentro(
  id: string,
  payload: UpdateEncuentroPayload,
): Promise<InstanciaEncuentro> {
  const response = await api.put<InstanciaEncuentro>(`/encuentros/${id}`, payload);
  return response.data;
}

export async function generateEmbed(
  materiaId: string,
  formato: 'html' | 'markdown',
): Promise<EmbedSnippetResponse> {
  const response = await api.post<EmbedSnippetResponse>(
    `/materias/${materiaId}/encuentros/embed`,
    { formato },
  );
  return response.data;
}
