export interface UsuarioResponse {
  id: string;
  nombre: string;
  apellidos: string;
  email: string;
  roles: string[];
  facturador: boolean;
  regional: string | null;
  legajo: string | null;
  legajo_profesional: string | null;
  banco: string | null;
  activo: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface UsuarioCreatePayload {
  email: string;
  nombre: string;
  apellidos: string;
  password?: string;
  roles: string[];
  facturador: boolean;
  regional?: string;
  legajo?: string;
  legajo_profesional?: string;
  banco?: string;
}

export interface UsuarioUpdatePayload {
  email?: string;
  nombre?: string;
  apellidos?: string;
  password?: string;
  roles?: string[];
  facturador?: boolean;
  regional?: string;
  legajo?: string;
  legajo_profesional?: string;
  banco?: string;
  activo?: boolean;
}

export const ROLES_DISPONIBLES = [
  'ADMIN',
  'COORDINADOR',
  'PROFESOR',
  'TUTOR',
  'NEXO',
  'FINANZAS',
  'ALUMNO',
] as const;

export type RolNombre = (typeof ROLES_DISPONIBLES)[number];
