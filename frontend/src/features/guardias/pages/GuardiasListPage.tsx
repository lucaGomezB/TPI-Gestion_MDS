import { useState, type ReactNode } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGuardias } from '../hooks/useGuardias';
import GuardiaTable from '../components/GuardiaTable';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import type { EstadoGuardia } from '../types/guardiaTypes';

function GuardiasListPage(): ReactNode {
  const { id: materiaId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [estadoFilter, setEstadoFilter] = useState<EstadoGuardia | ''>('');

  const { data, isLoading, isError, error, refetch } = useGuardias(materiaId || '', {
    estado: estadoFilter || undefined,
    page: 1,
  });

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message={(error as Error)?.message} onRetry={refetch} />;

  const dataArr = data?.data || [];

  return (
    <div>
      <PageHeader
        title="Guardias"
        breadcrumbs={[
          { label: 'Materias', href: '/materias' },
          { label: 'Guardias' },
        ]}
        actions={[
          {
            label: 'Nueva guardia',
            onClick: () => navigate(`/materias/${materiaId}/guardias/nuevo`),
            variant: 'primary',
          },
        ]}
      />

      <div className="mb-4">
        <select
          value={estadoFilter}
          onChange={(e) => setEstadoFilter(e.target.value as EstadoGuardia | '')}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">Todos los estados</option>
          <option value="Pendiente">Pendiente</option>
          <option value="Paga">Paga</option>
          <option value="Anulada">Anulada</option>
        </select>
      </div>

      {dataArr.length === 0 ? (
        <EmptyState
          title="No hay guardias registradas"
          description="Aún no hay guardias registradas para esta materia."
          actionLabel="Registrar primera guardia"
          onAction={() => navigate(`/materias/${materiaId}/guardias/nuevo`)}
        />
      ) : (
        <GuardiaTable data={dataArr} />
      )}
    </div>
  );
}

export default GuardiasListPage;
