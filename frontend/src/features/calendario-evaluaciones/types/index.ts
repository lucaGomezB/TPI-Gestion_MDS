import { z } from 'zod';

// --- Task 1.1: tipoEvaluacionEnum and evaluationDateSchema ---

export const tipoEvaluacionEnum = ['Parcial', 'TP', 'Coloquio'] as const;

export const evaluationDateSchema = z.object({
  id: z.string().uuid().optional(),
  materia_id: z.string().uuid('La materia es requerida'),
  cohorte_id: z.string().uuid('La cohorte es requerida'),
  tipo: z.enum(['Parcial', 'TP', 'Coloquio']),
  numero_instancia: z.number().int().min(1, 'La instancia debe ser al menos 1'),
  fecha: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Formato de fecha inválido (YYYY-MM-DD)'),
  titulo: z.string().min(1, 'El titulo es requerido').max(200, 'Máximo 200 caracteres'),
});

// --- Task 1.2: Derived types ---

export type EvaluationDate = z.infer<typeof evaluationDateSchema>;

export type CreateEvaluationDateData = Omit<EvaluationDate, 'id'>;

export type UpdateEvaluationDateData = Partial<CreateEvaluationDateData>;

// --- Task 1.3: Query params type ---

export interface EvaluacionesQueryParams {
  materia_id?: string;
  cohorte_id?: string;
}
