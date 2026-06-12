import { type ReactNode } from 'react';
import type { Guardia } from '../types/guardiaTypes';

const estadoColors: Record<string, string> = {
  Pendiente: 'bg-yellow-100 text-yellow-800',
  Paga: 'bg-green-100 text-green-800',
  Anulada: 'bg-red-100 text-red-800',
};

interface GuardiaTableProps {
  data: Guardia[];
}

function GuardiaTable({ data }: GuardiaTableProps): ReactNode {
  if (data.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Día</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Horario</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Comentarios</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha de creación</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((guardia) => (
            <tr key={guardia.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{guardia.dia}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{guardia.horario}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${estadoColors[guardia.estado] || 'bg-gray-100 text-gray-800'}`}>
                  {guardia.estado}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{guardia.comentarios || '—'}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{new Date(guardia.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default GuardiaTable;
