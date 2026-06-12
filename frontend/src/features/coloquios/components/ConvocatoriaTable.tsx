import { type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { ConvocatoriaColoquio } from '../types/coloquioTypes';

interface ConvocatoriaTableProps {
  data: ConvocatoriaColoquio[];
  onCerrar?: (id: string) => void;
}

function ConvocatoriaTable({ data, onCerrar }: ConvocatoriaTableProps): ReactNode {
  if (data.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Materia</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Título</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Días</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Convocados</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reservas</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cupos libres</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((conv) => (
            <tr key={conv.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{conv.materia_nombre}</td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900">{conv.titulo}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{conv.dias?.length || 0}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{conv.total_convocados}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{conv.reservas_activas}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{conv.cupos_libres}</td>
              <td className="px-4 py-3 text-sm space-x-3">
                <Link to={`/coloquios/${conv.id}/agenda`} className="text-blue-600 hover:text-blue-800">
                  Ver agenda
                </Link>
                <Link to={`/coloquios/${conv.id}/resultados`} className="text-blue-600 hover:text-blue-800">
                  Resultados
                </Link>
                {onCerrar && (
                  <button
                    onClick={() => onCerrar(conv.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Cerrar
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

export default ConvocatoriaTable;
