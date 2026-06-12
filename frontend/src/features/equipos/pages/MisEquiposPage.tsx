import { useState, useMemo, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useMisEquipos } from '../hooks/useMisEquipos';
import type { MisEquiposItem } from '../types/asignaciones';

const ESTADOS = ['Todos', 'Vigente', 'Pendiente', 'Vencida'] as const;

function MisEquiposPage(): ReactNode {
  const [filterEstado, setFilterEstado] = useState('Todos');
  const [filterRol, setFilterRol] = useState('');

  const { data: equipos, isLoading, error, refetch } = useMisEquipos();

  // Extract unique roles from data for filter
  const rolesDisponibles = useMemo(() => {
    if (!equipos) return [];
    return [...new Set(equipos.map((e) => e.rol))];
  }, [equipos]);

  // Apply filters
  const filtered = useMemo(() => {
    if (!equipos) return [];
    return equipos.filter((item) => {
      if (filterEstado !== 'Todos' && item.estado !== filterEstado) return false;
      if (filterRol && item.rol !== filterRol) return false;
      return true;
    });
  }, [equipos, filterEstado, filterRol]);

  if (isLoading) return <Loading />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  if (!equipos || equipos.length === 0) {
    return (
      <div>
        <PageHeader title="Mis Equipos" breadcrumbs={[{ label: 'Académico' }, { label: 'Mis Equipos' }]} />
        <EmptyState
          title="No tienes asignaciones activas"
          description="Actualmente no tienes equipos docentes asignados."
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Mis Equipos" breadcrumbs={[{ label: 'Académico' }, { label: 'Mis Equipos' }]} />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div>
          <select
            value={filterEstado}
            onChange={(e) => setFilterEstado(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {ESTADOS.map((est) => (
              <option key={est} value={est}>
                {est === 'Todos' ? 'Todos los estados' : est}
              </option>
            ))}
          </select>
        </div>
        <div>
          <select
            value={filterRol}
            onChange={(e) => setFilterRol(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los roles</option>
            {rolesDisponibles.map((rol) => (
              <option key={rol} value={rol}>
                {rol}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-white rounded-lg shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Materia</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Carrera</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Cohorte</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Comisiones</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Rol</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Responsable</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Vigencia</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-sm text-gray-700">{item.materia_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.carrera_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.cohorte_nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {item.comisiones?.join(', ') || '-'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{item.rol}</td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {item.responsable_nombre || '-'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  <span className="text-xs">
                    {item.vig_desde} - {item.vig_hasta}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">
                  <span
                    className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                      item.estado === 'Vigente'
                        ? 'bg-green-100 text-green-700'
                        : item.estado === 'Pendiente'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {item.estado}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-gray-500 text-center mt-4">
          No se encontraron asignaciones con los filtros seleccionados.
        </p>
      )}
    </div>
  );
}

export default MisEquiposPage;
