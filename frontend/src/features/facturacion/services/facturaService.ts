import api from '@/shared/services/api';
import type { FacturaListResponse, FacturaDetail } from '../types';

// ── Admin ──────────────────────────────────────────────────────────────

export interface AdminFacturaParams {
  estado?: string;
  periodo?: string;
  usuario_id?: string;
  q?: string;
  page?: number;
  page_size?: number;
}

export async function listFacturasAdmin(params: AdminFacturaParams): Promise<FacturaListResponse> {
  const response = await api.get<FacturaListResponse>('/admin/facturas', { params });
  return response.data;
}

export async function abonarFactura(id: string, descargar = false): Promise<FacturaDetail> {
  const response = await api.put<FacturaDetail>(`/admin/facturas/${id}/abonar`, null, {
    params: { descargar },
  });
  return response.data;
}

export async function descargarFacturaAdmin(id: string): Promise<void> {
  const response = await api.get(`/admin/facturas/${id}/descargar`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `factura-${id}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function descargarMiFactura(id: string): Promise<void> {
  const response = await api.get(`/docentes/facturas/${id}/descargar`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `factura-${id}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// ── Docente ────────────────────────────────────────────────────────────

export interface DocenteFacturaParams {
  periodo?: string;
  page?: number;
  page_size?: number;
}

export async function listMisFacturas(params: DocenteFacturaParams): Promise<FacturaListResponse> {
  const response = await api.get<FacturaListResponse>('/docentes/facturas', { params });
  return response.data;
}

export async function subirFactura(formData: FormData): Promise<void> {
  await api.post('/docentes/facturas', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
