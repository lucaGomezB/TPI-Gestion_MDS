import { useState, useMemo, type ReactNode } from 'react';
import type { RankingItem } from '../types';

const positionColors: Record<number, string> = {
  1: 'text-yellow-500',
  2: 'text-gray-400',
  3: 'text-amber-600',
};

interface RankingTableProps {
  items: RankingItem[];
  showOnlyApproved?: boolean;
}

function RankingTable({ items, showOnlyApproved = false }: RankingTableProps): ReactNode {
  const [sortConfig, setSortConfig] = useState<{ key: keyof RankingItem; dir: 'asc' | 'desc' }>({
    key: 'actividades_aprobadas',
    dir: 'desc',
  });

  const filtered = useMemo(() => {
    if (!showOnlyApproved) return items;
    return items.filter((i) => i.actividades_aprobadas >= 1);
  }, [items, showOnlyApproved]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.dir === 'desc' ? bVal - aVal : aVal - bVal;
      }
      return 0;
    });
  }, [filtered, sortConfig]);

  const handleSort = (key: keyof RankingItem) => {
    setSortConfig((prev) => ({
      key,
      dir: prev.key === key && prev.dir === 'desc' ? 'asc' : 'desc',
    }));
  };

  const SortIcon = ({ columnKey }: { columnKey: keyof RankingItem }) => {
    if (sortConfig.key !== columnKey) {
      return (
        <svg className="w-3 h-3 text-gray-300 inline-block ml-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
        </svg>
      );
    }
    return sortConfig.dir === 'asc' ? (
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
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
            <th className={thClass} onClick={() => handleSort('nombre')}>
              Nombre <SortIcon columnKey="nombre" />
            </th>
            <th className={thClass} onClick={() => handleSort('apellidos')}>
              Apellidos <SortIcon columnKey="apellidos" />
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comision</th>
            <th className={thClass} onClick={() => handleSort('actividades_aprobadas')}>
              Aprobadas <SortIcon columnKey="actividades_aprobadas" />
            </th>
            <th className={thClass} onClick={() => handleSort('total_actividades')}>
              Total <SortIcon columnKey="total_actividades" />
            </th>
            <th className={thClass} onClick={() => handleSort('porcentaje')}>
              Porcentaje <SortIcon columnKey="porcentaje" />
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sorted.map((item, index) => {
            const position = index + 1;
            return (
              <tr key={item.alumno_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">
                  <span className={`font-bold text-lg ${positionColors[position] || 'text-gray-500'}`}>
                    {position}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">{item.nombre}</td>
                <td className="px-4 py-3 text-sm text-gray-900">{item.apellidos}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{item.comision}</td>
                <td className="px-4 py-3 text-sm font-medium text-green-600">{item.actividades_aprobadas}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{item.total_actividades}</td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          item.porcentaje >= 75 ? 'bg-green-500' : item.porcentaje >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(item.porcentaje, 100)}%` }}
                      />
                    </div>
                    <span className={`font-medium text-xs w-8 text-right ${
                      item.porcentaje >= 50 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {item.porcentaje}%
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default RankingTable;
