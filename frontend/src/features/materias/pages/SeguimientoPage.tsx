import { useMemo, type ReactNode } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import { useSeguimiento } from '../services/useSeguimiento';
import { useExportAtrasados } from '../services/useReportes';
import FilterBar from '../components/FilterBar';
import CsvExportButton from '../components/CsvExportButton';
import MetricCard from '../components/MetricCard';
import PermissionDenied from '../components/PermissionDenied';
import type { FilterField } from '../components/FilterBar';

function SeguimientoPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const { data: materia } = useMateria(id!);
  const exportAtrasados = useExportAtrasados();

  const filters = {
    busqueda: searchParams.get('busqueda') || undefined,
    comision: searchParams.get('comision') || undefined,
    actividad: searchParams.get('actividad') || undefined,
    regional: searchParams.get('regional') || undefined,
    minimo_actividades: searchParams.get('minimo_actividades')
      ? Number(searchParams.get('minimo_actividades'))
      : undefined,
  };

  const { data: seguimiento, isLoading, error } = useSeguimiento(id!, filters);

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="atrasados:ver" />;
  }

  const filterFields: FilterField[] = [
    {
      key: 'comision',
      label: 'Comision',
      type: 'select',
      options: (materia?.comisiones || []).map((c) => ({ value: c, label: c })),
    },
    { key: 'busqueda', label: 'Busqueda', type: 'text', placeholder: 'Nombre, apellido o email' },
    { key: 'actividad', label: 'Actividad', type: 'text', placeholder: 'Filtrar por actividad' },
    { key: 'regional', label: 'Regional', type: 'text', placeholder: 'Filtrar por regional' },
    { key: 'minimo_actividades', label: 'Min. actividades', type: 'number', placeholder: '0' },
  ];

  const stats = useMemo(() => {
    if (!seguimiento || seguimiento.length === 0) return null;
    return {
      total: seguimiento.length,
      totalAprobadas: seguimiento.reduce((s, i) => s + i.total_aprobadas, 0),
      totalPendientes: seguimiento.reduce((s, i) => s + i.total_pendientes, 0),
      promedioAprobadas: (seguimiento.reduce((s, i) => s + i.total_aprobadas, 0) / seguimiento.length).toFixed(1),
    };
  }, [seguimiento]);

  return (
    <div>
      <PageHeader
        title="Seguimiento de alumnos"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia?.nombre || '...', href: `/materias/${id}` },
          { label: 'Seguimiento' },
        ]}
      />

      <FilterBar fields={filterFields} debounceMs={300} />

      {isLoading ? (
        <>
          <Loading skeleton />
          <Loading skeleton />
        </>
      ) : error ? (
        <ErrorDisplay message="Error al cargar datos de seguimiento" />
      ) : !seguimiento || seguimiento.length === 0 ? (
        <EmptyState
          title="No hay alumnos en esta materia"
          description="Los alumnos apareceran aqui cuando tengan actividades registradas."
        />
      ) : (
        <div>
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-4">
              <MetricCard label="Total Alumnos" value={stats.total} />
              <MetricCard label="Total Aprobadas" value={stats.totalAprobadas} />
              <MetricCard label="Total Pendientes" value={stats.totalPendientes} />
              <MetricCard label="Promedio Aprobadas" value={stats.promedioAprobadas} />
            </div>
          )}

          <div className="flex justify-end mb-4">
            <CsvExportButton
              onExport={() => exportAtrasados(id!)}
              label="Exportar CSV"
            />
          </div>

          <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Apellidos</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comision</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Aprobadas</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pendientes</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">% Aprobacion</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ultima Act.</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {seguimiento.map((item) => {
                  const pct = item.total_actividades > 0
                    ? Math.round((item.total_aprobadas / item.total_actividades) * 100)
                    : 0;
                  return (
                    <tr key={item.alumno_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{item.nombre}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{item.apellidos}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{item.comision}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{item.email}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{item.total_actividades}</td>
                      <td className="px-4 py-3 text-sm font-medium text-green-600">{item.total_aprobadas}</td>
                      <td className="px-4 py-3 text-sm font-medium text-red-600">{item.total_pendientes}</td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex items-center space-x-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-1.5 w-16">
                            <div
                              className={`h-1.5 rounded-full ${pct >= 75 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                              style={{ width: `${Math.min(pct, 100)}%` }}
                            />
                          </div>
                          <span className={`text-xs font-medium ${pct >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                            {pct}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">{item.ultima_actividad || '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default SeguimientoPage;
