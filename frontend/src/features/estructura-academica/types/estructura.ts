import { z } from 'zod';

// --- Carrera ---

export const carreraSchema = z.object({
  id: z.string().uuid().optional(),
  codigo: z.string().min(1, 'El código es requerido').max(20),
  nombre: z.string().min(1, 'El nombre es requerido').max(200),
  estado: z.enum(['Activa', 'Inactiva']).default('Activa'),
});

export const createCarreraSchema = carreraSchema.omit({ id: true, estado: true });
export const updateCarreraSchema = carreraSchema.pick({ nombre: true, estado: true });

export type Carrera = z.infer<typeof carreraSchema>;
export type CreateCarreraData = z.infer<typeof createCarreraSchema>;
export type UpdateCarreraData = z.infer<typeof updateCarreraSchema>;

// --- Cohorte ---

export const cohorteSchema = z.object({
  id: z.string().uuid().optional(),
  carrera_id: z.string().uuid('La carrera es requerida'),
  nombre: z.string().min(1, 'El nombre es requerido').max(100),
  anio_inicio: z.number().int().min(2000).max(2100),
  vig_desde: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  vig_hasta: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  estado: z.enum(['Activa', 'Inactiva']).default('Activa'),
});

export const createCohorteSchema = cohorteSchema.omit({ id: true, estado: true });
export const updateCohorteSchema = cohorteSchema.omit({ id: true });

export type Cohorte = z.infer<typeof cohorteSchema>;
export type CreateCohorteData = z.infer<typeof createCohorteSchema>;
export type UpdateCohorteData = z.infer<typeof updateCohorteSchema>;

// --- Materia ---

export const materiaSchema = z.object({
  id: z.string().uuid().optional(),
  codigo: z.string().min(1, 'El código es requerido').max(20),
  nombre: z.string().min(1, 'El nombre es requerido').max(200),
  estado: z.enum(['Activa', 'Inactiva']).default('Activa'),
});

export const createMateriaSchema = materiaSchema.omit({ id: true, estado: true });
export const updateMateriaSchema = materiaSchema.pick({ nombre: true, estado: true });

export type Materia = z.infer<typeof materiaSchema>;
export type CreateMateriaData = z.infer<typeof createMateriaSchema>;
export type UpdateMateriaData = z.infer<typeof updateMateriaSchema>;

// --- ProgramaMateria ---

export const programaMateriaSchema = z.object({
  id: z.string().uuid().optional(),
  materia_id: z.string().uuid(),
  carrera_id: z.string().uuid(),
  cohorte_id: z.string().uuid(),
  titulo: z.string().min(1, 'El título es requerido').max(200),
  filename: z.string(),
  upload_date: z.string().optional(),
});

export const uploadProgramaSchema = z.object({
  materia_id: z.string().uuid('La materia es requerida'),
  carrera_id: z.string().uuid('La carrera es requerida'),
  cohorte_id: z.string().uuid('La cohorte es requerida'),
  titulo: z.string().min(1, 'El título es requerido').max(200),
  file: z
    .instanceof(File)
    .refine((f) => f.type === 'application/pdf', 'Solo se aceptan archivos PDF')
    .refine((f) => f.size <= 10 * 1024 * 1024, 'El archivo no debe superar los 10MB'),
});

export type ProgramaMateria = z.infer<typeof programaMateriaSchema>;
export type UploadProgramaData = z.infer<typeof uploadProgramaSchema>;
