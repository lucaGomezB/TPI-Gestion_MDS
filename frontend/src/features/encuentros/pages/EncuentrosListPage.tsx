import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useEncuentros } from '../hooks/useEncuentros';
import EncuentroTable from '../components/EncuentroTable';
import EncuentroFilters from '../components/EncuentroFilters';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import type { EstadoEncuentro } from '../types/encuentroTypes';

function EncuentrosListPage(): ReactNode {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useEncuentros({ page: 1 });

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message={(error as Error)?.message} onRetry={refetch} />;

  const dataArr = data?.data || [];

  return (
    <div>
      <PageHeader
        title="Mis Encuentros"
        actions={[{ label: 'Nuevo encuentro', onClick: () => navigate('/encuentros/nuevo'), variant: 'primary' }]}
      />

      {dataArr.length === 0 ? (
        <EmptyState
          title="No hay encuentros"
          description="Aún no tiene encuentros registrados. Cree su primer encuentro."
          actionLabel="Crear encuentro"
          onAction={() => navigate('/encuentros/nuevo')}
        />
      ) : (
        <>
          <EncuentroFilters
            materiaOptions={[]}
            filters={{}}
            onChange={() => {}}
          />
          <EncuentroTable data={dataArr} />
        </>
      )}
    </div>
  );
}

export default EncuentrosListPage;
