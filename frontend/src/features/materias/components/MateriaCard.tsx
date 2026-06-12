import type { ReactNode } from 'react';
import type { MateriaKPI } from '../types';

interface MateriaCardProps {
  kpi: MateriaKPI;
  onClick?: () => void;
}

function MateriaCard({ kpi, onClick }: MateriaCardProps): ReactNode {
  if (kpi.error) {
    return (
      <div className="bg-white rounded-lg border border-red-200 p-4">
        <h3 className="font-semibold text-gray-900 mb-2">{kpi.materia.nombre}</h3>
        <p className="text-sm text-red-600">{kpi.error}</p>
      </div>
    );
  }

  return (
    <button
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow text-left w-full"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{kpi.materia.nombre}</h3>
          <p className="text-sm text-gray-500">{kpi.materia.cohorte}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          {kpi.atrasados_count} atrasados
        </span>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          {kpi.pendientes_count} pendientes
        </span>
        {kpi.proximo_examen && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {kpi.proximo_examen}
          </span>
        )}
      </div>
    </button>
  );
}

export default MateriaCard;
