import { useState, type ReactNode } from 'react';

interface ResultadoModalProps {
  isOpen: boolean;
  alumnoNombre: string;
  onClose: () => void;
  onConfirm: (data: { nota: number; aprobado: boolean }) => void;
  isSubmitting: boolean;
}

function ResultadoModal({ isOpen, alumnoNombre, onClose, onConfirm, isSubmitting }: ResultadoModalProps): ReactNode {
  const [nota, setNota] = useState<number>(0);
  const [aprobado, setAprobado] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm({ nota, aprobado });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Registrar resultado - {alumnoNombre}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nota</label>
            <input
              type="number"
              min={0}
              max={10}
              step={0.5}
              value={nota}
              onChange={(e) => setNota(Number(e.target.value))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              required
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="aprobado"
              checked={aprobado}
              onChange={(e) => setAprobado(e.target.checked)}
              className="rounded border-gray-300"
            />
            <label htmlFor="aprobado" className="text-sm text-gray-700">Aprobado</label>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Guardando...' : 'Confirmar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ResultadoModal;
