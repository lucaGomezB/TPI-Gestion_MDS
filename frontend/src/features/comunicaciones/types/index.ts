// ─── Comunicaciones (envío masivo) ───
// Backend schemas: PreviewRequest, PreviewItem, PreviewResponse,
//   EnviarRequest, LoteResponse, ComunicacionResponse, AprobarRequest

export type EstadoComunicacion =
  | 'Pendiente'
  | 'Enviando'
  | 'Enviado'
  | 'Fallido'
  | 'Cancelado';

/** Backend LoteResponse — batch summary for status tracking. */
export interface Comunicacion {
  id: string;
  materia_id: string;
  total: number;
  enviados: number;
  fallidos: number;
  estado: string;
  requiere_aprobacion: boolean;
  created_at: string;
}

/** Backend PreviewRequest — no extra fields (extra='forbid'). */
export interface ComunicacionPreviewRequest {
  asunto: string;
  cuerpo: string;
  alumno_ids?: string[];
}

/** Backend PreviewResponse — returns previews array. */
export interface ComunicacionPreviewResponse {
  previews: Array<{
    alumno_nombre: string;
    email_preview: string;
    asunto_renderizado: string;
    cuerpo_renderizado: string;
  }>;
}

/** Backend EnviarRequest — requires preview_confirmado. */
export interface ComunicacionEnviarRequest {
  asunto: string;
  cuerpo: string;
  preview_confirmado: boolean;
  alumno_ids?: string[];
}

/** Backend AprobarRequest — note: 'motivo' not 'motivo_rechazo'. */
export interface AprobarComunicacionRequest {
  accion: 'aprobar' | 'rechazar';
  motivo?: string;
}

// ─── Avisos (tablón) ───
// Backend schemas: AvisoCreate, AvisoUpdate, AvisoResponse, AckResponse
// Enums: AlcanceAviso (Global|PorMateria|PorCohorte|PorRol),
//        SeveridadAviso (Baja|Media|Alta|Critico)

export type AlcanceAviso = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol';
export type SeveridadAviso = 'Baja' | 'Media' | 'Alta' | 'Critico';

/** Backend AvisoResponse — from_attributes, includes ack_count. */
export interface Aviso {
  id: string;
  tenant_id: string;
  alcance: string;
  materia_id?: string | null;
  cohorte_id?: string | null;
  rol_destino?: string | null;
  severidad: string;
  titulo: string;
  cuerpo: string;
  inicio_en: string;
  fin_en: string;
  orden: number;
  activo: boolean;
  requiere_ack: boolean;
  created_at: string;
  updated_at: string;
  ack_count: number;
}

/** Backend AvisoCreate — used for both create and form data. */
export interface AvisoFormData {
  titulo: string;
  cuerpo: string;
  alcance: AlcanceAviso;
  materia_id?: string;
  cohorte_id?: string;
  rol_destino?: string;
  severidad: SeveridadAviso;
  inicio_en: string;
  fin_en: string;
  orden?: number;
  activo?: boolean;
  requiere_ack?: boolean;
}

/** Backend AckResponse. */
export interface AcknowledgmentAviso {
  acknowledged: boolean;
  leido_en: string;
}

// ─── Mensajería interna ───
// Backend schemas: MensajeCreate, MensajeResponder, MensajeResponse,
//   HiloResponse, InboxItemResponse, InboxResponse

/** Backend InboxItemResponse — thread summary. */
export interface HiloMensaje {
  hilo_id: string;
  asunto: string;
  ultimo_mensaje: string;
  ultima_fecha: string;
  remitente_nombre: string;
  no_leidos: number;
}

/** Backend MensajeResponse. */
export interface Mensaje {
  id: string;
  hilo_id: string;
  remitente_id: string;
  destinatario_id: string;
  asunto: string;
  cuerpo: string;
  leido: boolean;
  created_at: string;
}

/** Backend HiloResponse — returned by GET /mensajes/{id}. */
export interface HiloResponse {
  hilo_id: string;
  asunto: string;
  participantes: string[];
  mensajes: Mensaje[];
}

/** Backend MensajeCreate — note: destinatario_id, cuerpo (not receptor_id, contenido). */
export interface MensajeRequest {
  destinatario_id: string;
  asunto: string;
  cuerpo: string;
}

/** Backend MensajeResponder — note: cuerpo (not contenido). */
export interface ResponderMensajeRequest {
  cuerpo: string;
}
