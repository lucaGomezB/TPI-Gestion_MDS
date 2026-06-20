import api from '@/shared/services/api';
import type {
  Comunicacion,
  ComunicacionPreviewRequest,
  ComunicacionPreviewResponse,
  ComunicacionEnviarRequest,
  AprobarComunicacionRequest,
} from '../types';

/** GET /materias/{id}/comunicaciones — materiaId is REQUIRED path param. */
export async function getComunicaciones(materiaId: string): Promise<Comunicacion[]> {
  const response = await api.get<Comunicacion[]>(`/materias/${materiaId}/comunicaciones`);
  return response.data;
}

/** POST /materias/{id}/comunicaciones/preview — body matches PreviewRequest (no materia_id!). */
export async function previewComunicacion(
  materiaId: string,
  data: ComunicacionPreviewRequest,
): Promise<ComunicacionPreviewResponse> {
  const response = await api.post<ComunicacionPreviewResponse>(
    `/materias/${materiaId}/comunicaciones/preview`,
    data,
  );
  return response.data;
}

/** POST /materias/{id}/comunicaciones/enviar — body must include preview_confirmado. */
export async function enviarComunicacion(
  materiaId: string,
  data: ComunicacionEnviarRequest,
): Promise<Comunicacion> {
  const response = await api.post<Comunicacion>(
    `/materias/${materiaId}/comunicaciones/enviar`,
    data,
  );
  return response.data;
}

/** PUT /admin/comunicaciones/{id}/aprobar — body: { accion, motivo }. */
export async function aprobarComunicacion(
  id: string,
  data: AprobarComunicacionRequest,
): Promise<Comunicacion> {
  const response = await api.put<Comunicacion>(`/admin/comunicaciones/${id}/aprobar`, data);
  return response.data;
}

/** PUT /comunicaciones/{id}/cancelar. */
export async function cancelarComunicacion(id: string): Promise<Comunicacion> {
  const response = await api.put<Comunicacion>(`/comunicaciones/${id}/cancelar`);
  return response.data;
}
