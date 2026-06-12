export interface SalarioBase {
  id: string;
  tenant_id: string;
  rol: string;
  monto: number;
  desde: string;
  hasta: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalarioBaseCreate {
  rol: string;
  monto: number;
  desde: string;
  hasta?: string | null;
}

export interface SalarioBaseUpdate {
  rol?: string;
  monto?: number;
  desde?: string;
  hasta?: string | null;
}

export interface SalarioPlus {
  id: string;
  tenant_id: string;
  grupo: string;
  rol: string;
  descripcion: string;
  monto: number;
  desde: string;
  hasta: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalarioPlusCreate {
  grupo: string;
  rol: string;
  descripcion: string;
  monto: number;
  desde: string;
  hasta?: string | null;
}

export interface SalarioPlusUpdate {
  grupo?: string;
  rol?: string;
  descripcion?: string;
  monto?: number;
  desde?: string;
  hasta?: string | null;
}

export interface GrupoMateria {
  id: string;
  tenant_id: string;
  grupo: string;
  descripcion: string | null;
  created_at: string;
  updated_at: string;
}

export interface GrupoMateriaCreate {
  grupo: string;
  descripcion?: string | null;
}

export interface GrupoMateriaUpdate {
  grupo?: string;
  descripcion?: string | null;
}

export interface MateriaGrupo {
  id: string;
  materia_id: string;
  grupo_id: string;
  tenant_id: string;
  created_at: string;
}

export interface MateriasAsignarRequest {
  materia_ids: string[];
}

export const ROLES_SALARIALES = ['COORDINADOR', 'NEXO', 'PROFESOR', 'TUTOR'] as const;
