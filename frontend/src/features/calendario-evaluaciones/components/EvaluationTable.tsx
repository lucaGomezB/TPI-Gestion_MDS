import type { ReactNode } from 'react';
import type { EvaluationDate } from '../types';

interface EvaluationTableProps {
  evaluaciones: EvaluationDate[];
  isLoading: boolean;
  error: Error | null;
  onEdit: (evaluacion: EvaluationDate) => void;
  onDelete: (id: string) => void;
  onRetry: () => void;
}

const tipoColors: Record<string, string> = {
  Parcial: 'bg-blue-100 text-blue-800',
  TP: 'bg-green-100 text-green-800',
  Coloquio: 'bg-purple-100 text-purple-800',
};

function EvaluationTable({
  evaluaciones,
  isLoading,
  error,
  onEdit,
  onDelete,
  onRetry,
}: EvaluationTableProps): ReactNode {
  // --- Task 7.1: Loading state ---
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 bg-gray-200 rounded" />
        ))}
      </div>
    );
  }

  // --- Task 7.2: Error state ---
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center" role="alert">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <p className="text-sm font-medium text-red-800 mb-4">{error.message || 'Error al cargar evaluaciones'}</p>
        <button
          onClick={onRetry}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  // --- Task 7.3: Empty state ---
  if (evaluaciones.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No hay evaluaciones registradas</h3>
        <p className="text-sm text-gray-500 mb-4">Cree la primera evaluacion usando el boton "Nueva Evaluacion".</p>
      </div>
    );
  }

  // --- Data state ---
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Materia</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instancia</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cohorte</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titulo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {evaluaciones.map((ev) => (
            <tr key={ev.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">
                {(ev as EvaluationDate & { materia_nombre?: string }).materia_nombre || '—'}
              </td>
              <td className="px-4 py-3">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${tipoColors[ev.tipo] || 'bg-gray-100 text-gray-800'}`}>
                  {ev.tipo}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-900">{ev.numero_instancia}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{ev.fecha}</td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {(ev as EvaluationDate & { cohorte_nombre?: string }).cohorte_nombre || '—'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">{ev.titulo}</td>
              <td className="px-4 py-3 text-sm space-x-2">
                <button
                  onClick={() => onEdit(ev)}
                  className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
                >
                  Editar
                </button>
                <button
                  onClick={() => onDelete(ev.id!)}
                  className="text-red-600 hover:text-red-800 font-medium transition-colors"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default EvaluationTable;
