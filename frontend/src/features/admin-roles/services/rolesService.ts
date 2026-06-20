import api from '../../../shared/services/api';
import type {
  RolResponse,
  RolCreatePayload,
  RolUpdatePayload,
  PermissionsResponse,
} from '../types';

export const rolesService = {
  async list(): Promise<RolResponse[]> {
    const response = await api.get<RolResponse[]>('/admin/roles');
    return response.data;
  },

  async getById(id: string): Promise<RolResponse> {
    const response = await api.get<RolResponse>(`/admin/roles/${id}`);
    return response.data;
  },

  async create(data: RolCreatePayload): Promise<RolResponse> {
    const response = await api.post<RolResponse>('/admin/roles', data);
    return response.data;
  },

  async update(id: string, data: RolUpdatePayload): Promise<RolResponse> {
    const response = await api.put<RolResponse>(`/admin/roles/${id}`, data);
    return response.data;
  },

  async remove(id: string): Promise<void> {
    await api.delete(`/admin/roles/${id}`);
  },

  async getPermissions(): Promise<PermissionsResponse> {
    const response = await api.get<PermissionsResponse>('/admin/permissions');
    return response.data;
  },
};
