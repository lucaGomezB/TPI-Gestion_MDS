import { useState, useCallback, type ReactNode } from 'react';
import { useAuditDashboard } from '../hooks/useAuditDashboard';
import AccionesPorDiaChart from '../components/AccionesPorDiaChart';
import DocenteInteracciones from '../components/DocenteInteracciones';
import PageHeader from '../../../shared/components/PageHeader';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';

function getDefaultDateRange(): { desde: string; hasta: string } {
  const today = new Date();
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const format = (d: Date) => d.toISOString().split('T')[0];
  return {
    desde: format(thirtyDaysAgo),
    hasta: format(today),
  };
}

function AuditDashboardPage(): ReactNode {
  const defaultRange = getDefaultDateRange();
  const [fechaDesde, setFechaDesde] = useState(defaultRange.desde);
  const [fechaHasta, setFechaHasta] = useState(defaultRange.hasta);

  const { data, isLoading, isError, error, refetch } = useAuditDashboard(
    fechaDesde,
    fechaHasta,
  );

  const handleFechaDesdeChange = useCallback((value: string) => {
    setFechaDesde(value);
  }, []);

  const handleFechaHastaChange = useCallback((value: string) => {
    setFechaHasta(value);
  }, []);

  return (
    <div className="p-6">
      <PageHeader
        title="Dashboard de Auditoría"
        breadcrumbs={[
          { label: 'Administración' },
          { label: 'Auditoría' },
          { label: 'Dashboard' },
        ]}
      />

      {/* Summary metrics cards */}
      {isLoading && !data && (
        <div className="mb-6">
          <Loading message="Cargando dashboard..." />
        </div>
      )}

      {isError && !data && (
        <div className="mb-6">
          <ErrorDisplay
            message={
              error instanceof Error
                ? error.message
                : 'Error al cargar el dashboard'
            }
            onRetry={() => refetch()}
          />
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-2xl font-bold text-gray-900">
              {data.total_acciones.toLocaleString('es-AR')}
            </p>
            <p className="text-sm text-gray-500">Total de acciones</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-2xl font-bold text-gray-900">
              {data.total_dias}
            </p>
            <p className="text-sm text-gray-500">Días con actividad</p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="text-2xl font-bold text-gray-900">
              {data.total_acciones > 0 && data.total_dias > 0
                ? Math.round(data.total_acciones / data.total_dias)
                : 0}
            </p>
            <p className="text-sm text-gray-500">
              Promedio de acciones / día
            </p>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="mb-6">
        <AccionesPorDiaChart
          data={data?.acciones_por_dia}
          isLoading={isLoading}
          isError={isError}
          error={error instanceof Error ? error : null}
          onRetry={() => refetch()}
          fecha_desde={fechaDesde}
          fecha_hasta={fechaHasta}
          onFechaDesdeChange={handleFechaDesdeChange}
          onFechaHastaChange={handleFechaHastaChange}
        />
      </div>

      {/* Teacher interaction panel */}
      <div>
        <DocenteInteracciones />
      </div>
    </div>
  );
}

export default AuditDashboardPage;
