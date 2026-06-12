import { type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { InstanciaEncuentro } from '../types/encuentroTypes';

const estadoColors: Record<string, string> = {
  Programado: 'bg-blue-100 text-blue-800',
  Realizado: 'bg-green-100 text-green-800',
  Cancelado: 'bg-red-100 text-red-800',
};

interface EncuentroTableProps {
  data: InstanciaEncuentro[];
  showMateria?: boolean;
}

function EncuentroTable({ data, showMateria = false }: EncuentroTableProps): ReactNode {
  if (data.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hora</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Título</th>
            {showMateria && (
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Materia</th>
            )}
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Enlace</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((encuentro) => (
            <tr key={encuentro.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{encuentro.fecha}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{encuentro.hora}</td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900">{encuentro.titulo}</td>
              {showMateria && (
                <td className="px-4 py-3 text-sm text-gray-500">{encuentro.materia_nombre}</td>
              )}
              <td className="px-4 py-3">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${estadoColors[encuentro.estado] || 'bg-gray-100 text-gray-800'}`}>
                  {encuentro.estado}
                </span>
              </td>
              <td className="px-4 py-3 text-sm">
                {encuentro.meet_url ? (
                  <a
                    href={encuentro.meet_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Abrir Meet
                  </a>
                ) : (
                  <span className="text-gray-400">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-sm">
                <Link
                  to={`/encuentros/${encuentro.id}/editar`}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  Editar
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default EncuentroTable;
