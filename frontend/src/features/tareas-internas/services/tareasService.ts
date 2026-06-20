import api from '../../../shared/services/api';
import type {
  TareaResponse,
  TareaCreatePayload,
  TareaEstadoUpdatePayload,
  ComentarioResponse,
  ComentarioCreatePayload,
} from '../types';

export const tareasService = {
  async list(estado?: string): Promise<TareaResponse[]> {
    const params = new URLSearchParams();
    if (estado) params.set('estado', estado);
    const response = await api.get<TareaResponse[]>(
      `/tareas${params.toString() ? `?${params.toString()}` : ''}`,
    );
    return response.data;
  },

  async create(data: TareaCreatePayload): Promise<TareaResponse> {
    const response = await api.post<TareaResponse>('/tareas', data);
    return response.data;
  },

  async changeEstado(
    id: string,
    data: TareaEstadoUpdatePayload,
  ): Promise<TareaResponse> {
    const response = await api.put<TareaResponse>(
      `/tareas/${id}/estado`,
      data,
    );
    return response.data;
  },

  async addComentario(
    tareaId: string,
    data: ComentarioCreatePayload,
  ): Promise<ComentarioResponse> {
    const response = await api.post<ComentarioResponse>(
      `/tareas/${tareaId}/comentarios`,
      data,
    );
    return response.data;
  },
};
