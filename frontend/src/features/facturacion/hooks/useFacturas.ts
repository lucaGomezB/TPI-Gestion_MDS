import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as facturaService from '../services/facturaService';
import type { AdminFacturaParams, DocenteFacturaParams } from '../services/facturaService';

// ── Admin hooks ────────────────────────────────────────────────────────

export function useFacturasAdmin(params: AdminFacturaParams) {
  return useQuery({
    queryKey: ['facturas', 'admin', params],
    queryFn: () => facturaService.listFacturasAdmin(params),
  });
}

export function useAbonarFactura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => facturaService.abonarFactura(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas'] });
    },
  });
}

// ── Docente hooks ──────────────────────────────────────────────────────

export function useMisFacturas(params: DocenteFacturaParams) {
  return useQuery({
    queryKey: ['facturas', 'docente', params],
    queryFn: () => facturaService.listMisFacturas(params),
  });
}

export function useSubirFactura() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) => facturaService.subirFactura(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facturas', 'docente'] });
    },
  });
}
