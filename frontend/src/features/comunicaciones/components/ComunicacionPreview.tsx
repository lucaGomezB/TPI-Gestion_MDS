import type { ReactNode } from 'react';
import type { ComunicacionPreviewResponse } from '../types';

interface ComunicacionPreviewProps {
  preview: ComunicacionPreviewResponse;
  onConfirm: () => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

function ComunicacionPreview({
  preview,
  onConfirm,
  onBack,
  isSubmitting = false,
}: ComunicacionPreviewProps): ReactNode {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Vista previa del mensaje</h3>

        <div className="border-b border-gray-200 pb-4 mb-4">
          <p className="text-sm text-gray-500 mb-1">Asunto:</p>
          <p className="text-base font-medium text-gray-900">{preview.asunto_renderizado}</p>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-1">Cuerpo:</p>
          <div className="text-sm text-gray-900 whitespace-pre-wrap bg-gray-50 rounded-md p-4">
            {preview.cuerpo_renderizado}
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
          <p className="text-sm font-medium text-blue-800 mb-2">
            Este mensaje será enviado a <strong>{preview.total_destinatarios}</strong> destinatario(s)
          </p>
          {preview.destinatarios_ejemplo.length > 0 && (
            <div className="text-sm text-blue-700">
              <p className="mb-1">Ejemplos de destinatarios:</p>
              <ul className="list-disc list-inside space-y-1">
                {preview.destinatarios_ejemplo.map((d, i) => (
                  <li key={i}>
                    {d.nombre} ({d.email})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          Volver y editar
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isSubmitting}
          className="px-6 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {isSubmitting ? 'Enviando...' : 'Confirmar envío'}
        </button>
      </div>
    </div>
  );
}

export default ComunicacionPreview;
