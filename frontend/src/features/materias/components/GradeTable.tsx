import { useState, type ReactNode } from 'react';
import type { Calificacion } from '../types';

interface GradeTableProps {
  items: Calificacion[];
  pageSize?: number;
}

function GradeTable({ items, pageSize = 20 }: GradeTableProps): ReactNode {
  const [page, setPage] = useState(0);
  const totalPages = Math.ceil(items.length / pageSize);
  const paginatedItems = items.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Apellidos</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comision</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actividad</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nota</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedItems.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">{item.nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-900">{item.apellidos}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{item.comision}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{item.actividad}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={`font-medium ${item.nota >= 4 ? 'text-green-600' : 'text-red-600'}`}>
                    {item.nota}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{item.fecha}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200">
          <p className="text-sm text-gray-700">
            Mostrando {page * pageSize + 1} a {Math.min((page + 1) * pageSize, items.length)} de {items.length}
          </p>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default GradeTable;
