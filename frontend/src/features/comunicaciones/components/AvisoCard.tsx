import type { ReactNode } from 'react';
import type { Aviso } from '../types';
import SeveridadBadge from './SeveridadBadge';

interface AvisoCardProps {
  aviso: Aviso;
  onAcknowledge?: (id: string) => void;
  acknowledged?: boolean;
  isProcessing?: boolean;
}

function AvisoCard({
  aviso,
  onAcknowledge,
  acknowledged = false,
  isProcessing = false,
}: AvisoCardProps): ReactNode {
  const borderColor =
    aviso.severidad === 'Critico'
      ? 'border-l-red-500'
      : aviso.severidad === 'Advertencia'
        ? 'border-l-yellow-500'
        : 'border-l-blue-500';

  return (
    <div className={`bg-white border border-gray-200 border-l-4 ${borderColor} rounded-lg p-5`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-base font-semibold text-gray-900">{aviso.titulo}</h3>
          <SeveridadBadge severidad={aviso.severidad} />
          <span className="text-xs text-gray-400 capitalize">{aviso.alcance}</span>
        </div>
        {aviso.requiere_acuse && !acknowledged && (
          <button
            onClick={() => onAcknowledge?.(aviso.id)}
            disabled={isProcessing}
            className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-50 transition-colors shrink-0"
          >
            {isProcessing ? '...' : 'Confirmar lectura'}
          </button>
        )}
        {aviso.requiere_acuse && acknowledged && (
          <span className="px-3 py-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-md">
            Leído
          </span>
        )}
      </div>
      <p className="text-sm text-gray-700 whitespace-pre-wrap">{aviso.contenido}</p>
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
        <span>
          Desde: {new Date(aviso.inicio_vigencia).toLocaleDateString('es-AR')}
        </span>
        <span>
          Hasta: {new Date(aviso.fin_vigencia).toLocaleDateString('es-AR')}
        </span>
      </div>
    </div>
  );
}

export default AvisoCard;
