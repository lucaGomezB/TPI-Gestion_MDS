export interface Liquidacion {
  id: string;
  tenant_id: string;
  cohorte_id: string;
  periodo: string;
  usuario_id: string;
  rol: string;
  comisiones: string[];
  monto_base: number;
  monto_plus: number;
  total: number;
  es_nexo: boolean;
  excluido_por_factura: boolean;
  estado: string;
  created_at: string;
  cerrada_at: string | null;
}

export interface LiquidacionDetail extends Liquidacion {
  desglose_base: Record<string, unknown>;
  desglose_plus: Array<Record<string, unknown>>;
}

export interface LiquidacionKPI {
  total_sin_factura: number;
  total_con_factura: number;
  total_general: number;
}

export interface LiquidacionListResponse {
  items: Liquidacion[];
  kpis: LiquidacionKPI;
  total: number;
  page: number;
  page_size: number;
}

export interface LiquidacionDetailResponse extends LiquidacionDetail {
  // inherits everything
}
