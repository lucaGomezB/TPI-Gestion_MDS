import api from '@/shared/services/api';
import type { Guardia, CreateGuardiaPayload, GuardiaFilters } from '../types/guardiaTypes';

export async function getGuardias(
  materiaId: string,
  filters: Partial<GuardiaFilters>,
): Promise<Guardia[]> {
  const response = await api.get<{ items: Guardia[]; total: number }>(
    `/materias/${materiaId}/guardias`,
    { params: filters },
  );
  return response.data.items || [];
}

export async function createGuardia(
  materiaId: string,
  payload: CreateGuardiaPayload,
): Promise<{ id: string }> {
  const response = await api.post<{ id: string }>(`/materias/${materiaId}/guardias`, payload);
  return response.data;
}
