import type { ReactNode } from 'react';
import type { AsignacionDisplay, AsignacionFilters } from '../types/asignaciones';

interface AsignacionTableProps {
  data: AsignacionDisplay[];
  filters: AsignacionFilters;
  onFilterChange: (filters: AsignacionFilters) => void;
  onEdit: (item: AsignacionDisplay) => void;
  onToggle: (item: AsignacionDisplay) => void;
}

function AsignacionTable({ data, filters, onFilterChange, onEdit, onToggle }: AsignacionTableProps): ReactNode {
  const handleFilter = (key: keyof AsignacionFilters, value: string) => {
    onFilterChange({ ...filters, [key]: value || undefined });
  };

  return (
    <div>
      {/* Filters */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
        <div>
          <input
            type="text"
            placeholder="Buscar docente..."
            value={filters.search || ''}
            onChange={(e) => handleFilter('search', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <select
            value={filters.materia_id || ''}
            onChange={(e) => handleFilter('materia_id', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas las materias</option>
          </select>
        </div>
        <div>
          <select
            value={filters.rol || ''}
            onChange={(e) => handleFilter('rol', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los roles</option>
            <option value="PROFESOR">Profesor</option>
            <option value="TUTOR">Tutor</option>
            <option value="NEXO">Nexo</option>
            <option value="COORDINADOR">Coordinador</option>
          </select>
        </div>
        <div>
          <select
            value={filters.estado || ''}
            onChange={(e) => handleFilter('estado', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los estados</option>
            <option value="Vigente">Vigente</option>
            <option value="Pendiente">Pendiente</option>
            <option value="Vencida">Vencida</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Docente</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Rol</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Materia</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Carrera</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Cohorte</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Comisiones</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Vigencia</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm text-gray-700">
                  {item.docente_nombre} {item.docente_apellidos}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.rol}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.materia_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.carrera_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.cohorte_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {item.comisiones?.join(', ') || '-'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  <span className="text-xs">{item.vig_desde} - {item.vig_hasta}</span>
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  <div className="flex items-center justify-end space-x-2">
                    <button
                      onClick={() => onToggle(item)}
                      className={`px-2 py-1 text-xs font-medium rounded-full transition-colors ${
                        item.activo
                          ? 'bg-green-100 text-green-700 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {item.activo ? 'Activa' : 'Inactiva'}
                    </button>
                    <button
                      onClick={() => onEdit(item)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                    >
                      Editar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default AsignacionTable;
