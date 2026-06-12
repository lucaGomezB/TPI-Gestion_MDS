import { useCallback, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMateria } from '../services/useMaterias';
import { useReportes } from '../services/useReportes';
import MetricCard from '../components/MetricCard';
import PermissionDenied from '../components/PermissionDenied';

function ReportesPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { data: materia } = useMateria(id!);
  const { data: reportes, isLoading, error, refetch, isFetching } = useReportes(id!);

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="reportes:ver" />;
  }

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  return (
    <div>
      <PageHeader
        title="Reportes rapidos"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: materia?.nombre || '...', href: `/materias/${id}` },
          { label: 'Reportes' },
        ]}
        actions={reportes ? [
          { label: isFetching ? 'Actualizando...' : 'Actualizar', onClick: handleRefresh, variant: 'secondary' },
        ] : undefined}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
              <div className="h-8 bg-gray-200 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : error ? (
        <ErrorDisplay message="Error al cargar reportes" onRetry={handleRefresh} />
      ) : !reportes ? (
        <EmptyState
          title="No hay datos disponibles para mostrar reportes"
          description="Importa calificaciones para ver los reportes."
          actionLabel="Ir a importar"
          onAction={() => window.location.href = `/materias/${id}`}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            label="Total Alumnos"
            value={reportes.total_alumnos}
          />
          <MetricCard
            label="Total Actividades"
            value={reportes.total_actividades}
          />
          <MetricCard
            label="Promedio General"
            value={reportes.promedio_general.toFixed(2)}
          />
          <MetricCard
            label="Aprobados"
            value={reportes.aprobados}
            trend="up"
            trendLabel={`${reportes.total_alumnos > 0 ? Math.round((reportes.aprobados / reportes.total_alumnos) * 100) : 0}% del total`}
          />
          <MetricCard
            label="Reprobados"
            value={reportes.reprobados}
            trend="down"
            trendLabel={`${reportes.total_alumnos > 0 ? Math.round((reportes.reprobados / reportes.total_alumnos) * 100) : 0}% del total`}
          />
          <MetricCard
            label="Atrasados"
            value={reportes.atrasados}
            trend="down"
            trendLabel={`${reportes.total_alumnos > 0 ? Math.round((reportes.atrasados / reportes.total_alumnos) * 100) : 0}% del total`}
          />
        </div>
      )}
    </div>
  );
}

export default ReportesPage;
