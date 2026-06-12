import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConvocatorias } from '../hooks/useConvocatorias';
import ConvocatoriaTable from '../components/ConvocatoriaTable';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';

function ColoquiosListPage(): ReactNode {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useConvocatorias();

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message={(error as Error)?.message} onRetry={refetch} />;

  const dataArr = data || [];

  return (
    <div>
      <PageHeader
        title="Convocatorias de coloquio"
        actions={[
          { label: 'Nueva convocatoria', onClick: () => navigate('/coloquios/nuevo'), variant: 'primary' },
        ]}
      />

      {dataArr.length === 0 ? (
        <EmptyState
          title="No hay convocatorias de coloquio activas"
          description="Cree la primera convocatoria para comenzar."
          actionLabel="Crear primera convocatoria"
          onAction={() => navigate('/coloquios/nuevo')}
        />
      ) : (
        <ConvocatoriaTable data={dataArr} />
      )}
    </div>
  );
}

export default ColoquiosListPage;
