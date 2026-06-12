import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { auditoriaService } from '../services/auditoriaService';
import type { AuditFilters } from '../types';
import { DEFAULT_PAGE_SIZE } from '../types';

function filtersFromParams(params: URLSearchParams): AuditFilters {
  return {
    q: params.get('q') || undefined,
    accion: params.get('accion') || undefined,
    actor_id: params.get('actor_id') || undefined,
    materia_id: params.get('materia_id') || undefined,
    ip: params.get('ip') || undefined,
    fecha_desde: params.get('fecha_desde') || undefined,
    fecha_hasta: params.get('fecha_hasta') || undefined,
    limit: Number(params.get('limit')) || DEFAULT_PAGE_SIZE,
    offset: Number(params.get('offset')) || 0,
  };
}

export function useAuditLog() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(() => filtersFromParams(searchParams), [searchParams]);

  const queryKey = ['auditoria', 'log', filters] as const;

  const query = useQuery({
    queryKey,
    queryFn: () => auditoriaService.search(filters),
    placeholderData: keepPreviousData,
  });

  const hasActiveFilters = useMemo(() => {
    return Boolean(
      filters.q ||
        filters.accion ||
        filters.actor_id ||
        filters.materia_id ||
        filters.ip ||
        filters.fecha_desde ||
        filters.fecha_hasta,
    );
  }, [filters]);

  const setFilters = useCallback(
    (updates: Partial<AuditFilters>) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        // Reset offset to 0 when filters change (unless offset is explicitly provided)
        if (!('offset' in updates)) {
          next.set('offset', '0');
        }
        for (const [key, value] of Object.entries(updates)) {
          if (value === undefined || value === null || value === '') {
            next.delete(key);
          } else {
            next.set(key, String(value));
          }
        }
        return next;
      });
    },
    [setSearchParams],
  );

  const clearFilters = useCallback(() => {
    setSearchParams(new URLSearchParams());
  }, [setSearchParams]);

  const goToPage = useCallback(
    (offset: number) => {
      setFilters({ offset });
    },
    [setFilters],
  );

  const changePageSize = useCallback(
    (limit: number) => {
      setFilters({ limit, offset: 0 });
    },
    [setFilters],
  );

  return {
    filters,
    setFilters,
    clearFilters,
    goToPage,
    changePageSize,
    hasActiveFilters,
    data: query.data,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
