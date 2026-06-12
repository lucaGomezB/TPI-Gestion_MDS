import { useMemo, type ReactNode } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMonitorGeneral, useExportMonitorGeneral } from '../services/useMonitorGeneral';
import { useMaterias } from '../services/useMaterias';
import FilterBar from '../components/FilterBar';
import MetricCard from '../components/MetricCard';
import CsvExportButton from '../components/CsvExportButton';
import PermissionDenied from '../components/PermissionDenied';
import type { FilterField } from '../components/FilterBar';
import type { MonitorGeneralFilters } from '../types';

function MonitorGeneralPage(): ReactNode {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: allMaterias } = useMaterias();
  const exportMonitorGeneral = useExportMonitorGeneral();

  const filters = {
    materia_id: searchParams.get('materia_id') || undefined,
    regional: searchParams.get('regional') || undefined,
    comision: searchParams.get('comision') || undefined,
    busqueda: searchParams.get('busqueda') || undefined,
    status: (searchParams.get('status') as MonitorGeneralFilters['status'] | undefined) || undefined,
  };

  const { data: items, isLoading, error, refetch, isFetching } = useMonitorGeneral(filters);

  if (!user || (user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="materias:monitor_general" />;
  }

  const filterFields: FilterField[] = [
    {
      key: 'materia_id',
      label: 'Materia',
      type: 'select',
      options: (allMaterias || []).map((m) => ({ value: m.id, label: m.nombre })),
    },
    { key: 'regional', label: 'Regional', type: 'text', placeholder: 'Filtrar por regional' },
    { key: 'comision', label: 'Comision', type: 'text', placeholder: 'Filtrar por comision' },
    { key: 'busqueda', label: 'Busqueda', type: 'text', placeholder: 'Materia, cohorte...' },
    {
      key: 'status',
      label: 'Estado',
      type: 'select',
      options: [
        { value: 'todos', label: 'Todos' },
        { value: 'con_atrasados', label: 'Con atrasados' },
        { value: 'sin_datos', label: 'Sin datos' },
      ],
    },
  ];

  const stats = useMemo(() => {
    if (!items || items.length === 0) return null;
    return {
      total: items.length,
      totalAlumnos: items.reduce((s, i) => s + i.total_alumnos, 0),
      totalAtrasados: items.reduce((s, i) => s + i.atrasados_count, 0),
      promedioGeneral: items.length > 0
        ? (items.reduce((s, i) => s + i.promedio_general, 0) / items.length).toFixed(1)
        : '0',
    };
  }, [items]);

  return (
    <div>
      <PageHeader
        title="Monitor General de Materias"
        breadcrumbs={[
          { label: 'Administracion', href: '/admin' },
          { label: 'Monitor General' },
        ]}
        actions={[
          { label: isFetching ? 'Actualizando...' : 'Actualizar', onClick: () => refetch(), variant: 'secondary' },
        ]}
      />

      <FilterBar fields={filterFields} debounceMs={300} />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
              <div className="h-8 bg-gray-200 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : error ? (
        <ErrorDisplay message="Error al cargar el monitor general" onRetry={() => refetch()} />
      ) : !items || items.length === 0 ? (
        <EmptyState
          title="No se encontraron materias"
          description={Object.values(filters).some(Boolean)
            ? 'No hay materias que coincidan con los filtros aplicados.'
            : 'No hay materias configuradas en el sistema.'}
        />
      ) : (
        <div>
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <MetricCard label="Materias" value={stats.total} />
              <MetricCard label="Total Alumnos" value={stats.totalAlumnos} />
              <MetricCard label="Total Atrasados" value={stats.totalAtrasados} />
              <MetricCard label="Promedio General" value={stats.promedioGeneral} />
            </div>
          )}

          <div className="flex justify-end mb-4">
            <CsvExportButton
              onExport={() => exportMonitorGeneral(filters)}
              label="Exportar CSV"
            />
          </div>

          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Materia</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cohorte</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comision</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alumnos</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actividades</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Promedio</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Aprobados</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reprobados</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Atrasados</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pendientes</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item) => (
                  <tr
                    key={`${item.materia_id}-${item.comision}`}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/materias/${item.materia_id}`)}
                  >
                    <td className="px-4 py-3 text-sm font-medium text-blue-600 hover:text-blue-800">
                      {item.materia_nombre}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{item.cohorte}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{item.comision}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">{item.total_alumnos}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{item.total_actividades}</td>
                    <td className="px-4 py-3 text-sm font-medium">{item.promedio_general.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm font-medium text-green-600">{item.aprobados}</td>
                    <td className="px-4 py-3 text-sm font-medium text-red-600">{item.reprobados}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        item.atrasados_count > 0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {item.atrasados_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{item.pendientes_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default MonitorGeneralPage;
