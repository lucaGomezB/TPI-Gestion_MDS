import { type ReactNode } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import MensajeInbox from '../components/MensajeInbox';
import { useHilosMensajes } from '../hooks/useMensajes';

function MensajesPage(): ReactNode {
  const { data: hilos, isLoading, isError, refetch } = useHilosMensajes();

  return (
    <div>
      <PageHeader
        title="Mensajería interna"
        breadcrumbs={[{ label: 'Mensajería' }]}
      />

      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Bandeja de entrada</h2>
        </div>
        <MensajeInbox
          hilos={hilos}
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
        />
      </div>
    </div>
  );
}

export default MensajesPage;
