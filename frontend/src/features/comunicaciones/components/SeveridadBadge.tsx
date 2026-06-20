import type { ReactNode } from 'react';
import type { SeveridadAviso } from '../types';

const severidadStyles: Record<string, string> = {
  Baja: 'bg-blue-100 text-blue-800',
  Media: 'bg-yellow-100 text-yellow-800',
  Alta: 'bg-orange-100 text-orange-800',
  Critico: 'bg-red-100 text-red-800',
};

const severidadLabels: Record<string, string> = {
  Baja: 'Baja',
  Media: 'Media',
  Alta: 'Alta',
  Critico: 'Crítico',
};

interface SeveridadBadgeProps {
  severidad: string;
}

function SeveridadBadge({ severidad }: SeveridadBadgeProps): ReactNode {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${severidadStyles[severidad] ?? 'bg-gray-100 text-gray-800'}`}
    >
      {severidadLabels[severidad] ?? severidad}
    </span>
  );
}

export default SeveridadBadge;
