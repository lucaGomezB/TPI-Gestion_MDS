import api from '@/shared/services/api';
import type {
  SalarioBase,
  SalarioBaseCreate,
  SalarioBaseUpdate,
  SalarioPlus,
  SalarioPlusCreate,
  SalarioPlusUpdate,
  GrupoMateria,
  GrupoMateriaCreate,
  GrupoMateriaUpdate,
  MateriaGrupo,
  MateriasAsignarRequest,
} from '../types';

// ── SalarioBase ────────────────────────────────────────────────────────

export async function listSalarioBase(): Promise<SalarioBase[]> {
  const response = await api.get<SalarioBase[]>('/admin/salarios/base');
  return response.data;
}

export async function getSalarioBase(id: string): Promise<SalarioBase> {
  const response = await api.get<SalarioBase>(`/admin/salarios/base/${id}`);
  return response.data;
}

export async function createSalarioBase(data: SalarioBaseCreate): Promise<SalarioBase> {
  const response = await api.post<SalarioBase>('/admin/salarios/base', data);
  return response.data;
}

export async function updateSalarioBase(id: string, data: SalarioBaseUpdate): Promise<SalarioBase> {
  const response = await api.put<SalarioBase>(`/admin/salarios/base/${id}`, data);
  return response.data;
}

// ── SalarioPlus ────────────────────────────────────────────────────────

export async function listSalarioPlus(): Promise<SalarioPlus[]> {
  const response = await api.get<SalarioPlus[]>('/admin/salarios/plus');
  return response.data;
}

export async function getSalarioPlus(id: string): Promise<SalarioPlus> {
  const response = await api.get<SalarioPlus>(`/admin/salarios/plus/${id}`);
  return response.data;
}

export async function createSalarioPlus(data: SalarioPlusCreate): Promise<SalarioPlus> {
  const response = await api.post<SalarioPlus>('/admin/salarios/plus', data);
  return response.data;
}

export async function updateSalarioPlus(id: string, data: SalarioPlusUpdate): Promise<SalarioPlus> {
  const response = await api.put<SalarioPlus>(`/admin/salarios/plus/${id}`, data);
  return response.data;
}

// ── GrupoMateria ───────────────────────────────────────────────────────

export async function listGruposMateria(): Promise<GrupoMateria[]> {
  const response = await api.get<GrupoMateria[]>('/admin/salarios/grupos');
  return response.data;
}

export async function getGrupoMateria(id: string): Promise<GrupoMateria> {
  const response = await api.get<GrupoMateria>(`/admin/salarios/grupos/${id}`);
  return response.data;
}

export async function createGrupoMateria(data: GrupoMateriaCreate): Promise<GrupoMateria> {
  const response = await api.post<GrupoMateria>('/admin/salarios/grupos', data);
  return response.data;
}

export async function updateGrupoMateria(id: string, data: GrupoMateriaUpdate): Promise<GrupoMateria> {
  const response = await api.put<GrupoMateria>(`/admin/salarios/grupos/${id}`, data);
  return response.data;
}

export async function getMateriasByGrupo(id: string): Promise<MateriaGrupo[]> {
  const response = await api.get<MateriaGrupo[]>(`/admin/salarios/grupos/${id}/materias`);
  return response.data;
}

export async function assignMateriasToGrupo(id: string, data: MateriasAsignarRequest): Promise<MateriaGrupo[]> {
  const response = await api.put<MateriaGrupo[]>(`/admin/salarios/grupos/${id}/materias`, data);
  return response.data;
}
