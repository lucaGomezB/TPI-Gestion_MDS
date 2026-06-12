import { z } from 'zod';

const diaSemanaEnum = z.enum(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']);
const estadoEncuentroEnum = z.enum(['Programado', 'Realizado', 'Cancelado']);

export const createSlotSchema = z.object({
  materia_id: z.string().min(1, 'La materia es obligatoria'),
  titulo: z.string().min(1, 'El título es obligatorio').max(255, 'Máximo 255 caracteres'),
  dia_semana: diaSemanaEnum,
  hora: z.string().min(1, 'La hora es obligatoria').regex(/^\d{2}:\d{2}$/, 'Formato HH:MM'),
  fecha_inicio: z.string().min(1, 'La fecha de inicio es obligatoria'),
  cant_semanas: z.coerce.number().int().min(0, 'Debe ser mayor o igual a 0'),
  meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
});

export const createUnicoSchema = z.object({
  materia_id: z.string().min(1, 'La materia es obligatoria'),
  titulo: z.string().min(1, 'El título es obligatorio').max(255, 'Máximo 255 caracteres'),
  fecha: z.string().min(1, 'La fecha es obligatoria'),
  hora: z.string().min(1, 'La hora es obligatoria').regex(/^\d{2}:\d{2}$/, 'Formato HH:MM'),
  meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
});

export const updateEncuentroSchema = z.object({
  estado: estadoEncuentroEnum.optional(),
  meet_url: z.string().url('URL inválida').optional().or(z.literal('')),
  video_url: z.string().url('URL inválida').optional().or(z.literal('')),
  comentario: z.string().max(1000, 'Máximo 1000 caracteres').optional(),
});

export type CreateSlotFormData = z.infer<typeof createSlotSchema>;
export type CreateUnicoFormData = z.infer<typeof createUnicoSchema>;
export type UpdateEncuentroFormData = z.infer<typeof updateEncuentroSchema>;
