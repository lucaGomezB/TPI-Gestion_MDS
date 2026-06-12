import { z } from 'zod';

// --- Asignacion ---

export const asignacionSchema = z.object({
  id: z.string().uuid().optional(),
  docente_id: z.string().uuid('El docente es requerido'),
  materia_id: z.string().uuid('La materia es requerida'),
  carrera_id: z.string().uuid('La carrera es requerida'),
  cohorte_id: z.string().uuid('La cohorte es requerida'),
  rol: z.string().min(1, 'El rol es requerido'),
  comisiones: z.array(z.string()).optional().default([]),
  responsable_id: z.string().uuid().optional().nullable().default(null),
  vig_desde: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  vig_hasta: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  activo: z.boolean().default(true),
});

export const createAsignacionSchema = asignacionSchema.omit({ id: true, activo: true });
export const updateAsignacionSchema = asignacionSchema.omit({ id: true });

export type Asignacion = z.infer<typeof asignacionSchema>;
export type CreateAsignacionData = z.infer<typeof createAsignacionSchema>;
export type UpdateAsignacionData = z.infer<typeof updateAsignacionSchema>;

// --- Asignacion Masiva ---

export const asignacionMasivaSchema = z.object({
  docente_ids: z.array(z.string().uuid()).min(1, 'Seleccione al menos un docente'),
  materia_id: z.string().uuid('La materia es requerida'),
  carrera_id: z.string().uuid('La carrera es requerida'),
  cohorte_id: z.string().uuid('La cohorte es requerida'),
  rol: z.string().min(1, 'El rol es requerido'),
  comisiones: z.array(z.string()).optional().default([]),
  responsable_id: z.string().uuid().optional().nullable().default(null),
  vig_desde: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  vig_hasta: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
});

export type AsignacionMasivaData = z.infer<typeof asignacionMasivaSchema>;

// --- Clone Equipo ---

export const cloneEquipoSchema = z.object({
  source_materia_id: z.string().uuid('La materia origen es requerida'),
  source_carrera_id: z.string().uuid('La carrera origen es requerida'),
  source_cohorte_id: z.string().uuid('La cohorte origen es requerida'),
  dest_materia_id: z.string().uuid('La materia destino es requerida'),
  dest_carrera_id: z.string().uuid('La carrera destino es requerida'),
  dest_cohorte_id: z.string().uuid('La cohorte destino es requerida'),
}).refine(
  (data) =>
    !(
      data.source_materia_id === data.dest_materia_id &&
      data.source_carrera_id === data.dest_carrera_id &&
      data.source_cohorte_id === data.dest_cohorte_id
    ),
  { message: 'El origen y destino deben ser diferentes' },
);

export type CloneEquipoData = z.infer<typeof cloneEquipoSchema>;

// --- Vigencia Bulk ---

export const vigenciaBulkSchema = z.object({
  materia_id: z.string().uuid('La materia es requerida'),
  carrera_id: z.string().uuid('La carrera es requerida'),
  cohorte_id: z.string().uuid('La cohorte es requerida'),
  vig_desde: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  vig_hasta: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
});

export type VigenciaBulkData = z.infer<typeof vigenciaBulkSchema>;

// --- Export Equipo ---

export const exportEquipoSchema = z.object({
  materia_id: z.string().uuid().optional(),
  carrera_id: z.string().uuid().optional(),
  cohorte_id: z.string().uuid().optional(),
}).refine(
  (data) => data.materia_id || data.carrera_id || data.cohorte_id,
  { message: 'Seleccione al menos un filtro' },
);

export type ExportEquipoData = z.infer<typeof exportEquipoSchema>;

// --- Asignacion Filters ---

export interface AsignacionFilters {
  materia_id?: string;
  carrera_id?: string;
  cohorte_id?: string;
  rol?: string;
  estado?: string;
  search?: string;
}

// --- Asignacion display (with joined data) ---

export interface AsignacionDisplay {
  id: string;
  docente_nombre: string;
  docente_apellidos: string;
  docente_email: string;
  materia_nombre: string;
  materia_codigo: string;
  carrera_nombre: string;
  cohorte_nombre: string;
  rol: string;
  comisiones: string[];
  responsable_nombre?: string;
  vig_desde: string;
  vig_hasta: string;
  activo: boolean;
}

// --- Mis equipos display ---

export interface MisEquiposItem {
  id: string;
  materia_nombre: string;
  carrera_nombre: string;
  cohorte_nombre: string;
  comisiones: string[];
  rol: string;
  responsable_nombre?: string;
  vig_desde: string;
  vig_hasta: string;
  estado: 'Vigente' | 'Pendiente' | 'Vencida';
}
