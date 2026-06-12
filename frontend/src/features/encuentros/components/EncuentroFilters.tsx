import { type ReactNode } from 'react';
import type { EstadoEncuentro } from '../types/encuentroTypes';

interface EncuentroFiltersProps {
  materiaOptions: { value: string; label: string }[];
  filters: {
    materia_id?: string;
    estado?: EstadoEncuentro | '';
    fecha_desde?: string;
    fecha_hasta?: string;
  };
  onChange: (filters: { materia_id?: string; estado?: EstadoEncuentro | ''; fecha_desde?: string; fecha_hasta?: string }) => void;
}

function EncuentroFilters({ materiaOptions, filters, onChange }: EncuentroFiltersProps): ReactNode {
  const estadoOptions: (EstadoEncuentro | '')[] = ['', 'Programado', 'Realizado', 'Cancelado'];

  return (
    <div className="flex flex-wrap gap-4 items-end mb-6">
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Materia</label>
        <select
          value={filters.materia_id || ''}
          onChange={(e) => onChange({ ...filters, materia_id: e.target.value || undefined })}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Todas</option>
          {materiaOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Estado</label>
        <select
          value={filters.estado || ''}
          onChange={(e) => onChange({ ...filters, estado: (e.target.value as EstadoEncuentro) || undefined })}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {estadoOptions.map((est) => (
            <option key={est} value={est}>{est || 'Todos'}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Desde</label>
        <input
          type="date"
          value={filters.fecha_desde || ''}
          onChange={(e) => onChange({ ...filters, fecha_desde: e.target.value || undefined })}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Hasta</label>
        <input
          type="date"
          value={filters.fecha_hasta || ''}
          onChange={(e) => onChange({ ...filters, fecha_hasta: e.target.value || undefined })}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>
    </div>
  );
}

export default EncuentroFilters;
