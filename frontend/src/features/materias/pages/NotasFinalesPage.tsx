import { useMemo, useState, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import { useNotasFinales, useExportNotasFinales } from '../services/useReportes';
import MetricCard from '../components/MetricCard';
import CsvExportButton from '../components/CsvExportButton';
import PermissionDenied from '../components/PermissionDenied';
import type { NotaFinal } from '../types';

type GroupBy = 'comision' | 'todas';

function NotasFinalesPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [groupBy, setGroupBy] = useState<GroupBy>('todas');
  const { data: materia } = useMateria(id!);
  const { data: notas, isLoading, error } = useNotasFinales(id!);
  const exportNotas = useExportNotasFinales();

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="reportes:notas_finales" />;
  }

  const groupedNotas = useMemo(() => {
    if (!notas) return {};
    if (groupBy === 'todas') return { 'Todas las comisiones': notas };
    return notas.reduce<Record<string, NotaFinal[]>>((acc, n) => {
      const key = n.comision || 'Sin comision';
      if (!acc[key]) acc[key] = [];
      acc[key].push(n);
      return acc;
    }, {});
  }, [notas, groupBy]);

  const globalPromedio = useMemo(() => {
    if (!notas || notas.length === 0) return 0;
    const sum = notas.reduce((acc, n) => acc + n.nota_final, 0);
    return Number((sum / notas.length).toFixed(2));
  }, [notas]);

  const globalAprobados = useMemo(
    () => (notas || []).filter((n) => n.estado === 'aprobado').length,
    [notas],
  );

  return (
    <div>
      <PageHeader
        title="Notas Finales"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia?.nombre || '...', href: `/materias/${id}` },
          { label: 'Notas Finales' },
        ]}
        actions={notas && notas.length > 0 ? [
          { label: 'Exportar CSV', onClick: () => exportNotas(id!), variant: 'primary' },
        ] : undefined}
      />

      {notas && notas.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <MetricCard label="Total Alumnos" value={notas.length} />
          <MetricCard label="Promedio General" value={globalPromedio} />
          <MetricCard label="Aprobados" value={globalAprobados} trend="up" trendLabel={`de ${notas.length} alumnos`} />
          <MetricCard label="Reprobados" value={notas.length - globalAprobados} trend="down" />
        </div>
      )}

      {isLoading ? (
        <Loading skeleton />
      ) : error ? (
        <ErrorDisplay message="Error al cargar notas finales" />
      ) : !notas || notas.length === 0 ? (
        <div>
          <EmptyState
            title="Aun no hay calificaciones para calcular notas finales"
            description="Importa calificaciones para generar las notas finales."
          />
        </div>
      ) : (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <label htmlFor="group-by-select" className="text-sm text-gray-600">
                Agrupar por:
              </label>
              <select
                id="group-by-select"
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value as GroupBy)}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="todas">Todas las comisiones</option>
                <option value="comision">Comision</option>
              </select>
            </div>
            <CsvExportButton onExport={() => exportNotas(id!)} label="Exportar CSV" />
          </div>

          {Object.entries(groupedNotas).map(([groupName, groupItems]) => (
            <div key={groupName} className="mb-6">
              <h3 className="text-base font-semibold text-gray-800 mb-2">
                {groupName}
                <span className="text-sm font-normal text-gray-500 ml-2">
                  ({groupItems.length} {groupItems.length === 1 ? 'alumno' : 'alumnos'})
                </span>
              </h3>
              <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Apellidos</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comision</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Act.</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nota Final</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {groupItems.map((n) => (
                      <tr key={`${groupName}-${n.alumno_id}`} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 text-sm text-gray-900">{n.nombre}</td>
                        <td className="px-4 py-3 text-sm text-gray-900">{n.apellidos}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{n.comision}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{n.total_actividades}</td>
                        <td className="px-4 py-3 text-sm font-medium">
                          <span className={`${n.nota_final >= 4 ? 'text-green-700' : 'text-red-700'}`}>
                            {n.nota_final.toFixed(2)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            n.estado === 'aprobado' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {n.estado === 'aprobado' ? 'Aprobado' : 'Reprobado'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default NotasFinalesPage;
