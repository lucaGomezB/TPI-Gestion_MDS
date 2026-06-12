import { z } from 'zod';

const diaSemanaEnum = z.enum(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']);

export const createGuardiaSchema = z.object({
  asignacion_id: z.string().min(1, 'La asignación es obligatoria'),
  carrera_id: z.string().min(1, 'La carrera es obligatoria'),
  cohorte_id: z.string().min(1, 'El cohorte es obligatorio'),
  dia: diaSemanaEnum,
  horario: z.string().min(1, 'El horario es obligatorio'),
  comentarios: z.string().max(500, 'Máximo 500 caracteres').optional(),
});

export type CreateGuardiaFormData = z.infer<typeof createGuardiaSchema>;
