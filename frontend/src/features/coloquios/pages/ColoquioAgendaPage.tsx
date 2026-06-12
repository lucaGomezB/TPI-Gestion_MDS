import { type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { useAgenda } from '../hooks/useAgenda';
import AgendaDayCard from '../components/AgendaDayCard';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';

function ColoquioAgendaPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error, refetch } = useAgenda(id || '');

  if (isLoading) return <Loading skeleton />;
  if (isError) {
    const statusCode = (error as { response?: { status?: number } })?.response?.status;
    const message = statusCode === 404
      ? 'Convocatoria no encontrada'
      : (error as Error)?.message;
    return <ErrorDisplay message={message} onRetry={refetch} />;
  }

  if (!data) return null;

  const dias = data.dias || [];

  return (
    <div>
      <PageHeader
        title={data.convocatoria.titulo}
        breadcrumbs={[
          { label: 'Coloquios', href: '/coloquios' },
          { label: data.convocatoria.materia_nombre },
          { label: 'Agenda' },
        ]}
      />

      <div className="mb-4 text-sm text-gray-500">
        Materia: <span className="font-medium text-gray-700">{data.convocatoria.materia_nombre}</span>
        {' | '}
        Estado: <span className={`font-medium ${data.convocatoria.activa ? 'text-green-600' : 'text-red-600'}`}>
          {data.convocatoria.activa ? 'Activa' : 'Cerrada'}
        </span>
      </div>

      {dias.length === 0 ? (
        <EmptyState title="Sin días disponibles" description="Esta convocatoria no tiene días configurados." />
      ) : (
        <div className="space-y-4">
          {dias.map((dia) => (
            <AgendaDayCard key={dia.id} dia={dia} />
          ))}
        </div>
      )}
    </div>
  );
}

export default ColoquioAgendaPage;
