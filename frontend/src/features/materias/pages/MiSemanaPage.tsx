import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueries } from '@tanstack/react-query';
import api from '@/shared/services/api';
import PageHeader from '@/shared/components/PageHeader';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { useAuth } from '@/features/auth/context/AuthContext';
import { useMaterias } from '../services/useMaterias';
import MateriaCard from '../components/MateriaCard';
import MetricCard from '../components/MetricCard';
import PermissionDenied from '../components/PermissionDenied';
import type { MateriaKPI, Atrasado, Reporte } from '../types';

function MiSemanaPage(): ReactNode {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: materias, isLoading: loadingMaterias, error: errorMaterias } = useMaterias();

  const kpiQueries = useQueries({
    queries: (materias || []).map((m) => ({
      queryKey: ['materia', m.id, 'dashboard-kpi'],
      queryFn: async () => {
        const [atrasadosRes, reportesRes] = await Promise.allSettled([
          api.get<Atrasado[]>(`/materias/${m.id}/atrasados`),
          api.get<Reporte>(`/materias/${m.id}/reportes`),
        ]);

        let proximo_examen: string | undefined;
        if (reportesRes.status === 'fulfilled') {
          // Attempt to extract proximo_examen if available from a custom header or field
          // This comes from an enriched endpoint in the backend
        }

        const atrasados_count = atrasadosRes.status === 'fulfilled' ? atrasadosRes.value.data.length : 0;
        const pendientes_count = reportesRes.status === 'fulfilled' ? reportesRes.value.data.atrasados : 0;
        const hasKpiError = atrasadosRes.status === 'rejected' || reportesRes.status === 'rejected';
        const error = hasKpiError ? 'Error al cargar datos' : undefined;

        return {
          materia: m,
          atrasados_count,
          pendientes_count,
          proximo_examen,
          error,
        } as MateriaKPI;
      },
      staleTime: 60 * 1000,
      retry: 1,
    })),
  });

  if (!user || (user.rol !== 'PROFESOR' && user.rol !== 'ADMIN' && user.rol !== 'COORDINADOR')) {
    return <PermissionDenied requiredPermission="calificaciones:ver" />;
  }

  if (loadingMaterias) {
    return (
      <div>
        <PageHeader title="Mi Semana" breadcrumbs={[{ label: 'Materias' }]} />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
              <div className="flex gap-2">
                <div className="h-6 bg-gray-200 rounded-full w-20" />
                <div className="h-6 bg-gray-200 rounded-full w-24" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (errorMaterias) {
    return (
      <div>
        <PageHeader title="Mi Semana" breadcrumbs={[{ label: 'Materias' }]} />
        <ErrorDisplay
          message="Error al cargar las materias"
          onRetry={() => navigate(0)}
        />
      </div>
    );
  }

  if (!materias || materias.length === 0) {
    return (
      <div>
        <PageHeader title="Mi Semana" breadcrumbs={[{ label: 'Materias' }]} />
        <EmptyState
          title="No tienes materias asignadas"
          description="Las materias asignadas a tu perfil apareceran aqui. Si crees que esto es un error, contacta al administrador."
        />
      </div>
    );
  }

  const kpis = kpiQueries.map((q) => q.data).filter(Boolean) as MateriaKPI[];
  const totalAtrasados = kpis.reduce((sum, k) => sum + (k.atrasados_count || 0), 0);
  const totalPendientes = kpis.reduce((sum, k) => sum + (k.pendientes_count || 0), 0);
  const failedKpis = kpiQueries.filter((q) => q.isError || q.data?.error).length;
  const hasAllFailed = failedKpis === materias.length;

  return (
    <div>
      <PageHeader title="Mi Semana" breadcrumbs={[{ label: 'Materias' }]} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Materias" value={materias.length} />
        <MetricCard label="Total Atrasados" value={totalAtrasados} />
        <MetricCard label="Total Pendientes" value={totalPendientes} />
      </div>

      {hasAllFailed ? (
        <div className="mb-4">
          <ErrorDisplay
            message="No se pudieron cargar los indicadores de las materias. Intente nuevamente mas tarde."
            onRetry={() => navigate(0)}
          />
        </div>
      ) : (
        <>
          {failedKpis > 0 && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-700 flex items-center space-x-2">
              <svg className="w-5 h-5 text-yellow-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span>
                {failedKpis === 1
                  ? 'Una materia tiene errores al cargar datos. Los demas indicadores se muestran normalmente.'
                  : `${failedKpis} materias tienen errores al cargar datos. Los demas indicadores se muestran normalmente.`}
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {kpis.map((kpi) => (
              <MateriaCard
                key={kpi.materia.id}
                kpi={kpi}
                onClick={() => navigate(`/materias/${kpi.materia.id}`)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default MiSemanaPage;
