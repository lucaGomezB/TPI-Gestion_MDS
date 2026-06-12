import { Link } from 'react-router-dom';
import type { Liquidacion } from '../types';

interface LiquidacionTableProps {
  items: Liquidacion[];
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount);
}

const estadoBadge: Record<string, string> = {
  abierta: 'bg-yellow-100 text-yellow-800',
  cerrada: 'bg-green-100 text-green-800',
};

function LiquidacionTable({ items }: LiquidacionTableProps) {
  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-gray-500">
        No se encontraron liquidaciones para el periodo seleccionado.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Docente</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Comisiones</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Base</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Plus</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Accion</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {items.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">{item.usuario_id}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{item.rol}</td>
              <td className="px-4 py-3 text-sm text-gray-700">
                {item.comisiones.length > 0 ? item.comisiones.join(', ') : '-'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-700 text-right">{formatCurrency(item.monto_base)}</td>
              <td className="px-4 py-3 text-sm text-gray-700 text-right">{formatCurrency(item.monto_plus)}</td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">{formatCurrency(item.total)}</td>
              <td className="px-4 py-3 text-center">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${estadoBadge[item.estado] || 'bg-gray-100 text-gray-800'}`}>
                  {item.estado}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  to={`/liquidaciones/${item.id}`}
                  className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Ver detalle
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default LiquidacionTable;
