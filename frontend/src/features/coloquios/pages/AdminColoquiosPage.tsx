import { type ReactNode } from 'react';
import { useMetricas } from '../hooks/useMetricas';
import MetricasCards from '../components/MetricasCards';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';

function AdminColoquiosPage(): ReactNode {
  const { data, isLoading, isError, error, refetch } = useMetricas();

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message={(error as Error)?.message} onRetry={refetch} />;

  return (
    <div>
      <PageHeader title="Panel de coloquios" />
      {data ? (
        <MetricasCards metricas={data} />
      ) : null}
    </div>
  );
}

export default AdminColoquiosPage;
