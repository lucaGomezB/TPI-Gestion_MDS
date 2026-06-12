import type { ReactNode } from 'react';
import type { Comunicacion } from '../types';
import EstadoBadge from './EstadoBadge';
import Loading from '@/shared/components/Loading';
import EmptyState from '@/shared/components/EmptyState';
import ErrorDisplay from '@/shared/components/ErrorDisplay';

interface ComunicacionTrackingTableProps {
  comunicaciones: Comunicacion[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  onCancelar?: (id: string) => void;
}

function ComunicacionTrackingTable({
  comunicaciones,
  isLoading,
  isError,
  onRetry,
  onCancelar,
}: ComunicacionTrackingTableProps): ReactNode {
  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar comunicaciones" onRetry={onRetry} />;
  if (!comunicaciones || comunicaciones.length === 0) {
    return (
      <EmptyState
        title="Sin comunicaciones"
        description="No hay comunicaciones enviadas todavía. Cree una nueva para comenzar."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Asunto
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Estado
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Destinatarios
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Progreso
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Fecha
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {comunicaciones.map((com) => (
            <tr key={com.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-6 py-4 text-sm font-medium text-gray-900">{com.asunto}</td>
              <td className="px-6 py-4">
                <EstadoBadge estado={com.estado} />
              </td>
              <td className="px-6 py-4 text-sm text-gray-600">{com.destinatarios_count}</td>
              <td className="px-6 py-4">
                {com.estado === 'Enviado' || com.estado === 'Enviando' ? (
                  <div className="flex items-center gap-2">
                    <div className="w-full bg-gray-200 rounded-full h-2 max-w-[120px]">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{
                          width: `${com.destinatarios_count > 0 ? Math.round((com.enviados_count / com.destinatarios_count) * 100) : 0}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {com.enviados_count}/{com.destinatarios_count}
                    </span>
                  </div>
                ) : com.estado === 'Fallido' ? (
                  <span className="text-xs text-red-600">
                    {com.fallidos_count} fallidos
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">—</span>
                )}
              </td>
              <td className="px-6 py-4 text-sm text-gray-500">
                {new Date(com.created_at).toLocaleDateString('es-AR')}
              </td>
              <td className="px-6 py-4 text-right">
                {(com.estado === 'Pendiente' || com.estado === 'Enviando') && onCancelar && (
                  <button
                    onClick={() => onCancelar(com.id)}
                    className="text-sm text-red-600 hover:text-red-800 transition-colors"
                  >
                    Cancelar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ComunicacionTrackingTable;
