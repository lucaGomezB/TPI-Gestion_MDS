import { type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import ComunicacionAprobacionCard from '../components/ComunicacionAprobacionCard';
import Loading from '@/shared/components/Loading';
import EmptyState from '@/shared/components/EmptyState';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import { useComunicaciones, useAprobarComunicacion } from '../hooks/useComunicaciones';

function AprobacionPage(): ReactNode {
  const { id: materiaId } = useParams<{ id: string }>();
  const { data: comunicaciones, isLoading, isError, refetch } = useComunicaciones(materiaId);
  const aprobarMutation = useAprobarComunicacion();

  const pendientes = comunicaciones?.filter((c) => c.estado === 'Pendiente' && c.requiere_aprobacion) ?? [];

  const handleAprobar = (id: string) => {
    aprobarMutation.mutate({ id, data: { accion: 'aprobar' } });
  };

  const handleRechazar = (id: string, motivo: string) => {
    aprobarMutation.mutate({ id, data: { accion: 'rechazar', motivo_rechazo: motivo } });
  };

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar comunicaciones" onRetry={() => refetch()} />;

  return (
    <div>
      <PageHeader
        title="Aprobación de envíos"
        breadcrumbs={[
          { label: 'Comunicaciones', href: '/comunicaciones' },
          { label: 'Aprobación' },
        ]}
      />

      {pendientes.length === 0 ? (
        <EmptyState
          title="Sin pendientes"
          description="No hay comunicaciones pendientes de aprobación."
        />
      ) : (
        <div className="space-y-4">
          {pendientes.map((com) => (
            <ComunicacionAprobacionCard
              key={com.id}
              comunicacion={com}
              onAprobar={handleAprobar}
              onRechazar={handleRechazar}
              isProcessing={aprobarMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default AprobacionPage;
