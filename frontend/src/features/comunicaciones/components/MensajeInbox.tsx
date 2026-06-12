import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { HiloMensaje } from '../types';
import Loading from '@/shared/components/Loading';
import EmptyState from '@/shared/components/EmptyState';
import ErrorDisplay from '@/shared/components/ErrorDisplay';

interface MensajeInboxProps {
  hilos: HiloMensaje[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
}

function MensajeInbox({ hilos, isLoading, isError, onRetry }: MensajeInboxProps): ReactNode {
  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar mensajes" onRetry={onRetry} />;
  if (!hilos || hilos.length === 0) {
    return (
      <EmptyState
        title="Bandeja vacía"
        description="No tiene mensajes. Cuando reciba mensajes aparecerán aquí."
      />
    );
  }

  return (
    <div className="divide-y divide-gray-200 border border-gray-200 rounded-lg overflow-hidden">
      {hilos.map((hilo) => (
        <Link
          key={hilo.id}
          to={`/mensajeria/${hilo.id}`}
          className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3
                className={`text-sm truncate ${
                  hilo.no_leidos > 0 ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'
                }`}
              >
                {hilo.asunto}
              </h3>
              {hilo.no_leidos > 0 && (
                <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-blue-600 rounded-full">
                  {hilo.no_leidos}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {hilo.participantes.map((p) => `${p.nombre} ${p.apellido}`).join(', ')}
            </p>
          </div>
          <div className="text-right ml-4 shrink-0">
            <p className="text-xs text-gray-400">
              {new Date(hilo.ultimo_mensaje_en).toLocaleDateString('es-AR')}
            </p>
            <p className="text-xs text-gray-400 truncate max-w-[200px] mt-1">
              {hilo.ultimo_mensaje}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
}

export default MensajeInbox;
