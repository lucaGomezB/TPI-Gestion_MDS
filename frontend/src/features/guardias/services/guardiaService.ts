import api from '@/shared/services/api';
import type { Guardia, CreateGuardiaPayload, GuardiaFilters, PaginatedResponse } from '../types/guardiaTypes';

export async function getGuardias(
  materiaId: string,
  filters: Partial<GuardiaFilters>,
): Promise<PaginatedResponse<Guardia>> {
  const response = await api.get<PaginatedResponse<Guardia>>(`/materias/${materiaId}/guardias`, {
    params: filters,
  });
  return response.data;
}

export async function createGuardia(
  materiaId: string,
  payload: CreateGuardiaPayload,
): Promise<{ id: string }> {
  const response = await api.post<{ id: string }>(`/materias/${materiaId}/guardias`, payload);
  return response.data;
}
