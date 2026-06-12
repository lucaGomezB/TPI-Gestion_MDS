import api from '@/shared/services/api';
import type { LiquidacionListResponse, LiquidacionDetailResponse } from '../types';

export interface LiquidacionListParams {
  periodo: string;
  cohorte_id?: string;
  page?: number;
  page_size?: number;
}

export async function listLiquidaciones(params: LiquidacionListParams): Promise<LiquidacionListResponse> {
  const response = await api.get<LiquidacionListResponse>('/admin/liquidaciones', { params });
  return response.data;
}

export async function getLiquidacionDetail(id: string): Promise<LiquidacionDetailResponse> {
  const response = await api.get<LiquidacionDetailResponse>(`/admin/liquidaciones/${id}`);
  return response.data;
}

export async function cerrarLiquidacion(id: string): Promise<void> {
  await api.post(`/admin/liquidaciones/${id}/cerrar`);
}

export interface HistorialParams {
  periodo?: string;
  page?: number;
  page_size?: number;
}

export async function getHistorial(params: HistorialParams): Promise<LiquidacionListResponse> {
  const response = await api.get<LiquidacionListResponse>('/admin/liquidaciones/historial', { params });
  return response.data;
}
