import { type ReactNode } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import MensajeThread from '../components/MensajeThread';
import MensajeComposer from '../components/MensajeComposer';
import { useHiloMensaje, useResponderMensaje } from '../hooks/useMensajes';

function MensajeDetailPage(): ReactNode {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: hilo, isLoading, isError, refetch } = useHiloMensaje(id ?? '');
  const responderMutation = useResponderMensaje();

  const handleSend = async (contenido: string) => {
    if (!id) return;
    try {
      await responderMutation.mutateAsync({ hiloId: id, data: { cuerpo: contenido } });
    } catch {
      // Error handled by mutation
    }
  };

  const mensajes = hilo?.mensajes;

  if (!id) {
    navigate('/mensajeria');
    return null;
  }

  return (
    <div>
      <PageHeader
        title="Conversación"
        breadcrumbs={[
          { label: 'Mensajería', href: '/mensajeria' },
          { label: 'Conversación' },
        ]}
      />

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <MensajeThread
          mensajes={mensajes}
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
        />
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4 mt-4">
        <MensajeComposer
          onSend={handleSend}
          isSubmitting={responderMutation.isPending}
        />
      </div>
    </div>
  );
}

export default MensajeDetailPage;
