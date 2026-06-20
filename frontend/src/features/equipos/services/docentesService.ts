import api from '@/shared/services/api';
import type { Docente, CreateDocenteData, UpdateDocenteData } from '../types/docentes';

export async function getDocentes(): Promise<Docente[]> {
  const response = await api.get<Docente[]>('/admin/usuarios');
  return response.data;
}

export async function getDocente(id: string): Promise<Docente> {
  const response = await api.get<Docente>(`/admin/usuarios/${id}`);
  return response.data;
}

export async function createDocente(data: CreateDocenteData): Promise<Docente> {
  const response = await api.post<Docente>('/admin/usuarios', data);
  return response.data;
}

export async function updateDocente(id: string, data: UpdateDocenteData): Promise<Docente> {
  const response = await api.put<Docente>(`/admin/usuarios/${id}`, data);
  return response.data;
}
