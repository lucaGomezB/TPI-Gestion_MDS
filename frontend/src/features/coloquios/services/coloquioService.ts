import api from '@/shared/services/api';
import type {
  ConvocatoriaColoquio,
  CreateColoquioPayload,
  AgendaColoquio,
  ReservaColoquio,
  ResultadoColoquio,
  RegistrarResultadoPayload,
  ReservarTurnoPayload,
  MetricasColoquio,
} from '../types/coloquioTypes';

export async function getConvocatorias(
  params?: { materia_id?: string },
): Promise<ConvocatoriaColoquio[]> {
  const url = params?.materia_id
    ? `/materias/${params.materia_id}/coloquios`
    : '/coloquios';
  const response = await api.get<ConvocatoriaColoquio[]>(url);
  return response.data;
}

export async function createConvocatoria(
  payload: CreateColoquioPayload,
): Promise<{ id: string }> {
  const { materia_id, ...data } = payload;
  const response = await api.post<{ id: string }>(`/materias/${materia_id}/coloquios`, data);
  return response.data;
}

export async function getAgenda(id: string): Promise<AgendaColoquio> {
  const response = await api.get<AgendaColoquio>(`/coloquios/${id}/agenda`);
  return response.data;
}

export async function reservarTurno(
  coloquioId: string,
  payload: ReservarTurnoPayload,
): Promise<ReservaColoquio> {
  const response = await api.post<ReservaColoquio>(`/coloquios/${coloquioId}/reservar`, payload);
  return response.data;
}

export async function registrarResultado(
  coloquioId: string,
  payload: RegistrarResultadoPayload,
): Promise<ResultadoColoquio> {
  const response = await api.post<ResultadoColoquio>(
    `/coloquios/${coloquioId}/resultados`,
    payload,
  );
  return response.data;
}

export async function getMetricas(): Promise<MetricasColoquio> {
  const response = await api.get<MetricasColoquio>('/admin/coloquios/metricas');
  return response.data;
}
