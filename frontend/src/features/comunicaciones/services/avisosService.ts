import api from '@/shared/services/api';
import type { Aviso, AvisoFormData, AcknowledgmentAviso } from '../types';

/** GET /avisos — returns list of visible avisos for authenticated user. */
export async function getAvisos(): Promise<Aviso[]> {
  const response = await api.get<Aviso[]>('/avisos');
  return response.data;
}

/** GET /admin/avisos — returns { items, total } wrapper. */
export async function getAvisosAdmin(): Promise<Aviso[]> {
  const response = await api.get<{ items: Aviso[]; total: number }>('/admin/avisos');
  return response.data.items || [];
}

/** GET /admin/avisos/{id} — returns single aviso. */
export async function getAviso(id: string): Promise<Aviso> {
  const response = await api.get<Aviso>(`/admin/avisos/${id}`);
  return response.data;
}

/** POST /admin/avisos — expects AvisoCreate schema fields. */
export async function createAviso(data: AvisoFormData): Promise<Aviso> {
  const response = await api.post<Aviso>('/admin/avisos', data);
  return response.data;
}

/** PUT /admin/avisos/{id} — expects AvisoUpdate schema fields (partial). */
export async function updateAviso(id: string, data: Partial<AvisoFormData>): Promise<Aviso> {
  const response = await api.put<Aviso>(`/admin/avisos/${id}`, data);
  return response.data;
}

/** DELETE /admin/avisos/{id} — deactivates aviso. */
export async function deleteAviso(id: string): Promise<void> {
  await api.delete(`/admin/avisos/${id}`);
}

/** POST /avisos/{id}/ack — acknowledge reading. */
export async function acknowledgeAviso(avisoId: string): Promise<AcknowledgmentAviso> {
  const response = await api.post<AcknowledgmentAviso>(`/avisos/${avisoId}/ack`);
  return response.data;
}

/** GET /admin/avisos/{id}/ack-status — returns total and acknowledged counts. */
export async function getAcknowledgmentStatus(avisoId: string): Promise<{
  total: number;
  acknowledged: number;
}> {
  const response = await api.get<{ total: number; acknowledged: number }>(
    `/admin/avisos/${avisoId}/ack-status`,
  );
  return response.data;
}
