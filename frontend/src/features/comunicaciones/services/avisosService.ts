import api from '@/shared/services/api';
import type { Aviso, AvisoFormData, AcknowledgmentAviso } from '../types';

export async function getAvisos(): Promise<Aviso[]> {
  const response = await api.get<Aviso[]>('/avisos');
  return response.data;
}

export async function getAvisosAdmin(): Promise<Aviso[]> {
  const response = await api.get<Aviso[]>('/admin/avisos');
  return response.data;
}

export async function getAviso(id: string): Promise<Aviso> {
  const response = await api.get<Aviso>(`/admin/avisos/${id}`);
  return response.data;
}

export async function createAviso(data: AvisoFormData): Promise<Aviso> {
  const response = await api.post<Aviso>('/admin/avisos', data);
  return response.data;
}

export async function updateAviso(id: string, data: Partial<AvisoFormData>): Promise<Aviso> {
  const response = await api.put<Aviso>(`/admin/avisos/${id}`, data);
  return response.data;
}

export async function deleteAviso(id: string): Promise<void> {
  await api.delete(`/admin/avisos/${id}`);
}

export async function acknowledgeAviso(avisoId: string): Promise<AcknowledgmentAviso> {
  const response = await api.post<AcknowledgmentAviso>(`/avisos/${avisoId}/ack`);
  return response.data;
}

export async function getAcknowledgmentStatus(avisoId: string): Promise<{
  total: number;
  acknowledged: number;
}> {
  const response = await api.get<{ total: number; acknowledged: number }>(
    `/admin/avisos/${avisoId}/ack-status`,
  );
  return response.data;
}
