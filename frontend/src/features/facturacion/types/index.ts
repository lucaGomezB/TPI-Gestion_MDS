export interface Factura {
  id: string;
  tenant_id: string;
  usuario_id: string;
  periodo: string;
  detalle: string;
  referencia_archivo: string;
  tamano_kb: number;
  estado: string;
  cargada_at: string;
  abonada_at: string | null;
}

export interface FacturaDetail extends Factura {
  descargar_url: string | null;
}

export interface FacturaListResponse {
  items: Factura[];
  total: number;
  page: number;
  page_size: number;
}

export type FacturaFilterEstado = 'Pendiente' | 'Abonada' | '';
