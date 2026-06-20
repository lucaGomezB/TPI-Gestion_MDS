export interface RolResponse {
  id: string;
  nombre: string;
  descripcion: string | null;
  permisos: string[];
  activo: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface RolCreatePayload {
  nombre: string;
  descripcion?: string;
  permisos: string[];
}

export interface RolUpdatePayload {
  nombre?: string;
  descripcion?: string;
  permisos?: string[];
  activo?: boolean;
}

export interface ModuloPermisos {
  modulo: string;
  permisos: string[];
}

export interface PermissionsResponse {
  modulos: ModuloPermisos[];
  todos: string[];
}
