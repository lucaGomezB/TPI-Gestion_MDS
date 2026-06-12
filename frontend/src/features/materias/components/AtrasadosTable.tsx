import { useState, useMemo, type ReactNode } from 'react';
import type { Atrasado } from '../types';

const razonLabels: Record<string, string> = {
  faltante: 'Faltante',
  nota_baja: 'Nota baja',
};

const razonColors: Record<string, string> = {
  faltante: 'bg-orange-100 text-orange-800',
  nota_baja: 'bg-red-100 text-red-800',
};

type SortKey = 'nombre' | 'apellidos' | 'comision' | 'razon' | 'nota_minima' | 'umbral';
type SortDir = 'asc' | 'desc';

interface AtrasadosTableProps {
  items: Atrasado[];
  onSendReminder?: (alumnoId: string) => void;
}

function AtrasadosTable({ items, onSendReminder }: AtrasadosTableProps): ReactNode {
  const [sortKey, setSortKey] = useState<SortKey>('apellidos');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      let cmp = 0;
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal == null) cmp = 0;
      else if (aVal == null) cmp = 1;
      else if (bVal == null) cmp = -1;
      else cmp = String(aVal).localeCompare(String(bVal), 'es', { numeric: true });
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [items, sortKey, sortDir]);

  const SortIcon = ({ columnKey }: { columnKey: SortKey }) => {
    if (sortKey !== columnKey) {
      return (
        <svg className="w-3 h-3 text-gray-300 inline-block ml-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
        </svg>
      );
    }
    return sortDir === 'asc' ? (
      <svg className="w-3 h-3 text-blue-600 inline-block ml-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
      </svg>
    ) : (
      <svg className="w-3 h-3 text-blue-600 inline-block ml-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
      </svg>
    );
  };

  const thClass = "px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 select-none";

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className={thClass} onClick={() => handleSort('nombre')}>
              Nombre <SortIcon columnKey="nombre" />
            </th>
            <th className={thClass} onClick={() => handleSort('apellidos')}>
              Apellidos <SortIcon columnKey="apellidos" />
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
            <th className={thClass} onClick={() => handleSort('comision')}>
              Comision <SortIcon columnKey="comision" />
            </th>
            <th className={thClass} onClick={() => handleSort('razon')}>
              Razon <SortIcon columnKey="razon" />
            </th>
            <th className={thClass} onClick={() => handleSort('nota_minima')}>
              Nota Minima <SortIcon columnKey="nota_minima" />
            </th>
            <th className={thClass} onClick={() => handleSort('umbral')}>
              Umbral <SortIcon columnKey="umbral" />
            </th>
            {onSendReminder && <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sorted.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{item.nombre}</td>
              <td className="px-4 py-3 text-sm text-gray-900">{item.apellidos}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.email}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.comision}</td>
              <td className="px-4 py-3 text-sm">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${razonColors[item.razon] || 'bg-gray-100 text-gray-800'}`}>
                  {razonLabels[item.razon] || item.razon}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.nota_minima ?? '-'}</td>
              <td className="px-4 py-3 text-sm text-gray-500">{item.umbral}%</td>
              {onSendReminder && (
                <td className="px-4 py-3 text-sm">
                  <button
                    onClick={() => onSendReminder(item.alumno_id)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Enviar recordatorio
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AtrasadosTable;
