import { z } from 'zod';

export const diaColoquioSchema = z.object({
  fecha: z.string().min(1, 'La fecha es obligatoria'),
  cupos: z.coerce.number().int().min(1, 'Debe haber al menos 1 cupo'),
});

export const createColoquioSchema = z.object({
  materia_id: z.string().min(1, 'La materia es obligatoria'),
  titulo: z.string().min(1, 'El título es obligatorio').max(200, 'Máximo 200 caracteres'),
  dias: z.array(diaColoquioSchema).min(1, 'Debe agregar al menos un día disponible'),
});

export const registrarResultadoSchema = z.object({
  alumno_id: z.string().min(1),
  nota: z.coerce.number().min(0, 'La nota debe ser mayor o igual a 0').max(10, 'La nota máxima es 10'),
  aprobado: z.boolean(),
});

export type CreateColoquioFormData = z.infer<typeof createColoquioSchema>;
export type RegistrarResultadoFormData = z.infer<typeof registrarResultadoSchema>;
