import api from '@/shared/services/api';
import type {
  Carrera,
  CreateCarreraData,
  UpdateCarreraData,
  Cohorte,
  CreateCohorteData,
  UpdateCohorteData,
  Materia,
  CreateMateriaData,
  UpdateMateriaData,
  ProgramaMateria,
} from '../types/estructura';

// --- Carreras ---

export async function getCarreras(): Promise<Carrera[]> {
  const response = await api.get<Carrera[]>('/admin/carreras');
  return response.data;
}

export async function getCarrera(id: string): Promise<Carrera> {
  const response = await api.get<Carrera>(`/admin/carreras/${id}`);
  return response.data;
}

export async function createCarrera(data: CreateCarreraData): Promise<Carrera> {
  const response = await api.post<Carrera>('/admin/carreras', data);
  return response.data;
}

export async function updateCarrera(id: string, data: UpdateCarreraData): Promise<Carrera> {
  const response = await api.put<Carrera>(`/admin/carreras/${id}`, data);
  return response.data;
}

// --- Cohortes ---

export async function getCohortes(params?: { carrera_id?: string }): Promise<Cohorte[]> {
  const response = await api.get<Cohorte[]>('/admin/cohortes', { params });
  return response.data;
}

export async function getCohorte(id: string): Promise<Cohorte> {
  const response = await api.get<Cohorte>(`/admin/cohortes/${id}`);
  return response.data;
}

export async function createCohorte(data: CreateCohorteData): Promise<Cohorte> {
  const response = await api.post<Cohorte>('/admin/cohortes', data);
  return response.data;
}

export async function updateCohorte(id: string, data: UpdateCohorteData): Promise<Cohorte> {
  const response = await api.put<Cohorte>(`/admin/cohortes/${id}`, data);
  return response.data;
}

// --- Materias ---

export async function getMaterias(): Promise<Materia[]> {
  const response = await api.get<Materia[]>('/admin/materias');
  return response.data;
}

export async function getMateria(id: string): Promise<Materia> {
  const response = await api.get<Materia>(`/admin/materias/${id}`);
  return response.data;
}

export async function createMateria(data: CreateMateriaData): Promise<Materia> {
  const response = await api.post<Materia>('/admin/materias', data);
  return response.data;
}

export async function updateMateria(id: string, data: UpdateMateriaData): Promise<Materia> {
  const response = await api.put<Materia>(`/admin/materias/${id}`, data);
  return response.data;
}

// --- Programas ---

export async function uploadPrograma(
  materiaId: string,
  carreraId: string,
  cohorteId: string,
  titulo: string,
  file: File,
): Promise<ProgramaMateria> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('materia_id', materiaId);
  formData.append('carrera_id', carreraId);
  formData.append('cohorte_id', cohorteId);
  formData.append('titulo', titulo);

  const response = await api.post<ProgramaMateria>('/admin/programas-materia/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getProgramas(materiaId: string): Promise<ProgramaMateria[]> {
  const response = await api.get<ProgramaMateria[]>(`/admin/materias/${materiaId}/programas`);
  return response.data;
}

export async function downloadPrograma(programaId: string): Promise<Blob> {
  const response = await api.get(`/admin/programas-materia/${programaId}/download`, {
    responseType: 'blob',
  });
  return response.data;
}
