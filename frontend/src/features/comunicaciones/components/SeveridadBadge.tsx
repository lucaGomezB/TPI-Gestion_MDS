import type { ReactNode } from 'react';
import type { SeveridadAviso } from '../types';

const severidadStyles: Record<SeveridadAviso, string> = {
  Info: 'bg-blue-100 text-blue-800',
  Advertencia: 'bg-yellow-100 text-yellow-800',
  Critico: 'bg-red-100 text-red-800',
};

interface SeveridadBadgeProps {
  severidad: SeveridadAviso;
}

function SeveridadBadge({ severidad }: SeveridadBadgeProps): ReactNode {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${severidadStyles[severidad]}`}
    >
      {severidad === 'Critico' ? 'Crítico' : severidad}
    </span>
  );
}

export default SeveridadBadge;
