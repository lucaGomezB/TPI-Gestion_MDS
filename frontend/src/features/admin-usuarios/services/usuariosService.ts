import api from '../../../shared/services/api';
import type {
  UsuarioResponse,
  UsuarioCreatePayload,
  UsuarioUpdatePayload,
} from '../types';

export const usuariosService = {
  async list(rol?: string): Promise<UsuarioResponse[]> {
    const params = new URLSearchParams();
    if (rol) params.set('rol', rol);
    const response = await api.get<UsuarioResponse[]>(
      `/admin/usuarios${params.toString() ? `?${params.toString()}` : ''}`,
    );
    return response.data;
  },

  async getById(id: string): Promise<UsuarioResponse> {
    const response = await api.get<UsuarioResponse>(`/admin/usuarios/${id}`);
    return response.data;
  },

  async create(data: UsuarioCreatePayload): Promise<UsuarioResponse> {
    const response = await api.post<UsuarioResponse>('/admin/usuarios', data);
    return response.data;
  },

  async update(id: string, data: UsuarioUpdatePayload): Promise<UsuarioResponse> {
    const response = await api.put<UsuarioResponse>(`/admin/usuarios/${id}`, data);
    return response.data;
  },

  async deactivate(id: string): Promise<UsuarioResponse> {
    const response = await api.put<UsuarioResponse>(`/admin/usuarios/${id}`, {
      activo: false,
    });
    return response.data;
  },
};
