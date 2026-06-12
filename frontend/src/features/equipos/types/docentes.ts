import { z } from 'zod';

export const docenteSchema = z.object({
  id: z.string().uuid().optional(),
  nombre: z.string().min(1, 'El nombre es requerido').max(100),
  apellidos: z.string().min(1, 'Los apellidos son requeridos').max(200),
  email: z.string().email('Email inválido'),
  roles: z.array(z.string()).min(1, 'Seleccione al menos un rol'),
  regional: z.string().max(100).optional().default(''),
  activo: z.boolean().default(true),
});

export const createDocenteSchema = docenteSchema.omit({ id: true, activo: true });
export const updateDocenteSchema = docenteSchema.omit({ id: true });

export type Docente = z.infer<typeof docenteSchema>;
export type CreateDocenteData = z.infer<typeof createDocenteSchema>;
export type UpdateDocenteData = z.infer<typeof updateDocenteSchema>;

export const DOCENTE_ROLES = [
  { value: 'PROFESOR', label: 'Profesor' },
  { value: 'TUTOR', label: 'Tutor' },
  { value: 'NEXO', label: 'Nexo' },
  { value: 'COORDINADOR', label: 'Coordinador' },
] as const;

export const REGIONALES = [
  'Capital Federal',
  'Gran Buenos Aires',
  'Córdoba',
  'Rosario',
  'Mendoza',
  'Tucumán',
  'La Plata',
  'Mar del Plata',
  'Salta',
  'Santa Fe',
  'Corrientes',
  'Neuquén',
] as const;
