import { useState, type ReactNode } from 'react';
import type { Comunicacion, EstadoComunicacion } from '../types';
import EstadoBadge from './EstadoBadge';

interface ComunicacionAprobacionCardProps {
  comunicacion: Comunicacion;
  onAprobar: (id: string) => void;
  onRechazar: (id: string, motivo: string) => void;
  isProcessing?: boolean;
}

function ComunicacionAprobacionCard({
  comunicacion,
  onAprobar,
  onRechazar,
  isProcessing = false,
}: ComunicacionAprobacionCardProps): ReactNode {
  const [showRechazar, setShowRechazar] = useState(false);
  const [motivo, setMotivo] = useState('');

  const handleRechazar = () => {
    if (motivo.trim()) {
      onRechazar(comunicacion.id, motivo);
      setMotivo('');
      setShowRechazar(false);
    }
  };

  if (comunicacion.estado !== 'Pendiente') return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">Lote {comunicacion.id.substring(0, 8)}</h3>
            <EstadoBadge estado={comunicacion.estado as EstadoComunicacion} />
          </div>
          <p className="text-sm text-gray-500 mb-1">
            Total destinatarios: {comunicacion.total}
          </p>
          <p className="text-sm text-gray-500">
            Creado: {new Date(comunicacion.created_at).toLocaleDateString('es-AR')}
          </p>
        </div>
      </div>

      <div className="bg-gray-50 rounded-md p-4 mb-4">
        <p className="text-sm text-gray-700">
          Enviados: {comunicacion.enviados} / Fallidos: {comunicacion.fallidos}
        </p>
        {comunicacion.requiere_aprobacion && (
          <p className="text-sm text-yellow-700 mt-1">Requiere aprobación</p>
        )}
      </div>

      {!showRechazar ? (
        <div className="flex justify-end gap-3">
          <button
            onClick={() => setShowRechazar(true)}
            disabled={isProcessing}
            className="px-4 py-2 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-md hover:bg-red-50 disabled:opacity-50 transition-colors"
          >
            Rechazar
          </button>
          <button
            onClick={() => onAprobar(comunicacion.id)}
            disabled={isProcessing}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {isProcessing ? 'Procesando...' : 'Aprobar envío'}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <textarea
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Motivo del rechazo (obligatorio)"
          />
          <div className="flex justify-end gap-3">
            <button
              onClick={() => {
                setShowRechazar(false);
                setMotivo('');
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Volver
            </button>
            <button
              onClick={handleRechazar}
              disabled={!motivo.trim() || isProcessing}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {isProcessing ? 'Procesando...' : 'Confirmar rechazo'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComunicacionAprobacionCard;
