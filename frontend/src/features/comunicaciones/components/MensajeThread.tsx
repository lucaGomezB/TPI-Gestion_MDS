import { useRef, useEffect, type ReactNode } from 'react';
import type { Mensaje } from '../types';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';

interface MensajeThreadProps {
  mensajes: Mensaje[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
}

function MensajeThread({
  mensajes,
  isLoading,
  isError,
  onRetry,
}: MensajeThreadProps): ReactNode {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar mensajes" onRetry={onRetry} />;
  if (!mensajes || mensajes.length === 0) {
    return <p className="text-sm text-gray-500 text-center py-8">No hay mensajes en este hilo.</p>;
  }

  return (
    <div className="space-y-4">
      {mensajes.map((msg) => {
        const isOwn = msg.remitente_id === localStorage.getItem('user_id');
        return (
          <div
            key={msg.id}
            className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[75%] rounded-lg px-4 py-3 ${
                isOwn
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-xs font-medium mb-1 opacity-75">
                {isOwn ? 'Yo' : msg.remitente_id.substring(0, 8)}
              </p>
              <p className="text-sm whitespace-pre-wrap">{msg.cuerpo}</p>
              <p className={`text-xs mt-1 ${isOwn ? 'text-blue-200' : 'text-gray-400'}`}>
                {new Date(msg.created_at).toLocaleString('es-AR')}
              </p>
            </div>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}

export default MensajeThread;
