import { useState, type ReactNode } from 'react';
import { useEncuentros } from '../hooks/useEncuentros';
import EncuentroTable from '../components/EncuentroTable';
import EncuentroFilters from '../components/EncuentroFilters';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import type { EstadoEncuentro } from '../types/encuentroTypes';

function AdminEncuentrosPage(): ReactNode {
  const [filters, setFilters] = useState<{
    materia_id?: string;
    estado?: EstadoEncuentro | '';
    fecha_desde?: string;
    fecha_hasta?: string;
  }>({});

  const queryParams = {
    ...(filters.materia_id ? { materia_id: filters.materia_id } : {}),
    ...(filters.estado ? { estado: filters.estado as EstadoEncuentro } : {}),
    ...(filters.fecha_desde ? { fecha_desde: filters.fecha_desde } : {}),
    ...(filters.fecha_hasta ? { fecha_hasta: filters.fecha_hasta } : {}),
    page: 1,
  };

  const { data, isLoading, isError, error, refetch } = useEncuentros(queryParams);

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message={(error as Error)?.message} onRetry={refetch} />;

  const dataArr = data?.data || [];

  return (
    <div>
      <PageHeader title="Vista transversal de encuentros" />
      <EncuentroFilters filters={filters} onChange={setFilters} materiaOptions={[]} />
      {dataArr.length === 0 ? (
        <EmptyState title="No hay encuentros registrados" />
      ) : (
        <EncuentroTable data={dataArr} showMateria />
      )}
    </div>
  );
}

export default AdminEncuentrosPage;
