import { useState, type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import AvisoCard from '../components/AvisoCard';
import Loading from '@/shared/components/Loading';
import EmptyState from '@/shared/components/EmptyState';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import { useAvisos, useAcknowledgeAviso } from '../hooks/useAvisos';

const ACKNOWLEDGED_KEY = 'avisos_acknowledged';

function getAcknowledgedIds(): string[] {
  try {
    const stored = localStorage.getItem(ACKNOWLEDGED_KEY);
    return stored ? (JSON.parse(stored) as string[]) : [];
  } catch {
    return [];
  }
}

function saveAcknowledgedId(id: string) {
  const ids = getAcknowledgedIds();
  if (!ids.includes(id)) {
    ids.push(id);
    localStorage.setItem(ACKNOWLEDGED_KEY, JSON.stringify(ids));
  }
}

function AvisosPage(): ReactNode {
  const { data: avisos, isLoading, isError, refetch } = useAvisos();
  const acknowledgeMutation = useAcknowledgeAviso();
  const [acknowledgedIds, setAcknowledgedIds] = useState<string[]>(getAcknowledgedIds);

  const handleAcknowledge = async (id: string) => {
    try {
      await acknowledgeMutation.mutateAsync(id);
      saveAcknowledgedId(id);
      setAcknowledgedIds((prev) => [...prev, id]);
    } catch {
      // Error handled by mutation
    }
  };

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar avisos" onRetry={() => refetch()} />;
  if (!avisos || avisos.length === 0) {
    return (
      <div>
        <PageHeader title="Avisos" breadcrumbs={[{ label: 'Avisos' }]} />
        <EmptyState
          title="Sin avisos"
          description="No hay avisos activos en este momento."
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Avisos" breadcrumbs={[{ label: 'Avisos' }]} />

      <div className="space-y-4">
        {avisos.map((aviso) => (
          <AvisoCard
            key={aviso.id}
            aviso={aviso}
            onAcknowledge={handleAcknowledge}
            acknowledged={acknowledgedIds.includes(aviso.id)}
            isProcessing={acknowledgeMutation.isPending}
          />
        ))}
      </div>
    </div>
  );
}

export default AvisosPage;
