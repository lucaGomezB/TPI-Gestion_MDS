import { useState, useCallback, useEffect, type ReactNode } from 'react';
import type { AuditFilters as AuditFiltersType } from '../types';
import { ACCIONES_LABELS } from '../types';

interface AuditFiltersProps {
  filters: AuditFiltersType;
  onFilterChange: (updates: Partial<AuditFiltersType>) => void;
  onClear: () => void;
  hasActiveFilters: boolean;
}

function AuditFilters({
  filters,
  onFilterChange,
  onClear,
  hasActiveFilters,
}: AuditFiltersProps): ReactNode {
  const [searchInput, setSearchInput] = useState(filters.q || '');
  const [ipInput, setIpInput] = useState(filters.ip || '');

  useEffect(() => {
    setSearchInput(filters.q || '');
    setIpInput(filters.ip || '');
  }, [filters.q, filters.ip]);

  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      onFilterChange({ q: searchInput || undefined });
    },
    [searchInput, onFilterChange],
  );

  const handleIpChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setIpInput(value);
    },
    [],
  );

  const handleIpBlur = useCallback(() => {
    onFilterChange({ ip: ipInput || undefined });
  }, [ipInput, onFilterChange]);

  const inputClasses =
    'w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500';

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
      {/* Full-text search */}
      <form onSubmit={handleSearchSubmit} className="mb-4">
        <div className="relative">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Buscar en el log... (Enter para buscar)"
            className={`${inputClasses} pr-10`}
            aria-label="Búsqueda full-text"
          />
          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
            aria-label="Buscar"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
              />
            </svg>
          </button>
        </div>
      </form>

      {/* Filter grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Date from */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Fecha desde
          </label>
          <input
            type="date"
            value={filters.fecha_desde || ''}
            onChange={(e) =>
              onFilterChange({ fecha_desde: e.target.value || undefined })
            }
            className={inputClasses}
          />
        </div>

        {/* Date to */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Fecha hasta
          </label>
          <input
            type="date"
            value={filters.fecha_hasta || ''}
            onChange={(e) =>
              onFilterChange({ fecha_hasta: e.target.value || undefined })
            }
            className={inputClasses}
          />
        </div>

        {/* Action filter */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Acción
          </label>
          <select
            value={filters.accion || ''}
            onChange={(e) =>
              onFilterChange({ accion: e.target.value || undefined })
            }
            className={inputClasses}
          >
            <option value="">Todas las acciones</option>
            {Object.entries(ACCIONES_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {/* IP filter */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Dirección IP
          </label>
          <input
            type="text"
            value={ipInput}
            onChange={handleIpChange}
            onBlur={handleIpBlur}
            placeholder="Ej: 192.168.1.1"
            className={inputClasses}
          />
        </div>

        {/* User filter */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Usuario ID
          </label>
          <input
            type="text"
            value={filters.actor_id || ''}
            onChange={(e) =>
              onFilterChange({ actor_id: e.target.value || undefined })
            }
            placeholder="ID del usuario"
            className={inputClasses}
          />
        </div>

        {/* Materia filter */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Materia ID
          </label>
          <input
            type="text"
            value={filters.materia_id || ''}
            onChange={(e) =>
              onFilterChange({ materia_id: e.target.value || undefined })
            }
            placeholder="ID de la materia"
            className={inputClasses}
          />
        </div>
      </div>

      {/* Reset button */}
      {hasActiveFilters && (
        <div className="mt-3 flex justify-end">
          <button
            onClick={onClear}
            className="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Limpiar filtros
          </button>
        </div>
      )}
    </div>
  );
}

export default AuditFilters;
