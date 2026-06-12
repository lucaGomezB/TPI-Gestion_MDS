import type { ReactNode } from 'react';
import type { EstadoComunicacion } from '../types';

const estadoStyles: Record<EstadoComunicacion, string> = {
  Pendiente: 'bg-yellow-100 text-yellow-800',
  Enviando: 'bg-blue-100 text-blue-800',
  Enviado: 'bg-green-100 text-green-800',
  Fallido: 'bg-red-100 text-red-800',
  Cancelado: 'bg-gray-100 text-gray-600',
};

interface EstadoBadgeProps {
  estado: EstadoComunicacion;
}

function EstadoBadge({ estado }: EstadoBadgeProps): ReactNode {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${estadoStyles[estado]}`}
    >
      {estado}
    </span>
  );
}

export default EstadoBadge;
