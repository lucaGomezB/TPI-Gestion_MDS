import api from '@/shared/services/api';
import type {
  EvaluationDate,
  CreateEvaluationDateData,
  UpdateEvaluationDateData,
  EvaluacionesQueryParams,
} from '../types';

// --- Task 2.1: List evaluaciones ---

export async function getEvaluaciones(params?: EvaluacionesQueryParams): Promise<EvaluationDate[]> {
  const response = await api.get<EvaluationDate[]>('/evaluaciones', { params });
  return response.data;
}

// --- Task 2.2: Create evaluacion ---

export async function createEvaluacion(data: CreateEvaluationDateData): Promise<EvaluationDate> {
  const response = await api.post<EvaluationDate>('/evaluaciones', data);
  return response.data;
}

// --- Task 2.3: Update evaluacion ---

export async function updateEvaluacion(id: string, data: UpdateEvaluationDateData): Promise<EvaluationDate> {
  const response = await api.put<EvaluationDate>(`/evaluaciones/${id}`, data);
  return response.data;
}

// --- Task 2.4: Delete evaluacion ---

export async function deleteEvaluacion(id: string): Promise<void> {
  await api.delete(`/evaluaciones/${id}`);
}

// --- Task 2.5: Generate embed snippet ---

export async function generateEmbed(
  materia_id: string,
  formato: string = 'html',
): Promise<string> {
  const response = await api.post<{ snippet: string }>(
    `/materias/${materia_id}/evaluaciones/embed`,
    null,
    { params: { formato } },
  );
  return response.data.snippet;
}
