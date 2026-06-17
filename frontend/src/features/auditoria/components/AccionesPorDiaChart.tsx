import { type ReactNode } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { AccionesPorDia } from '../types';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';
import EmptyState from '../../../shared/components/EmptyState';

interface AccionesPorDiaChartProps {
  data: AccionesPorDia[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  onRetry?: () => void;
  fecha_desde: string;
  fecha_hasta: string;
  onFechaDesdeChange: (value: string) => void;
  onFechaHastaChange: (value: string) => void;
}

function AccionesPorDiaChart({
  data,
  isLoading,
  isError,
  error,
  onRetry,
  fecha_desde,
  fecha_hasta,
  onFechaDesdeChange,
  onFechaHastaChange,
}: AccionesPorDiaChartProps): ReactNode {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <Loading message="Cargando gráfico..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <ErrorDisplay
          message={error?.message || 'Error al cargar el gráfico'}
          onRetry={onRetry}
        />
      </div>
    );
  }

  const inputClasses =
    'px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500';

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Acciones por día
        </h3>
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={fecha_desde}
            onChange={(e) => onFechaDesdeChange(e.target.value)}
            className={inputClasses}
            aria-label="Fecha desde"
          />
          <span className="text-gray-400">-</span>
          <input
            type="date"
            value={fecha_hasta}
            onChange={(e) => onFechaHastaChange(e.target.value)}
            className={inputClasses}
            aria-label="Fecha hasta"
          />
        </div>
      </div>

      {!data || data.length === 0 ? (
        <EmptyState
          title="No hay datos de interacciones"
          description="No hay datos de interacciones en el período seleccionado."
        />
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="fecha"
                tick={{ fontSize: 12 }}
                tickFormatter={(val: string) => {
                  const d = new Date(val);
                  return d.toLocaleDateString('es-AR', {
                    day: '2-digit',
                    month: '2-digit',
                  });
                }}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                allowDecimals={false}
              />
              <Tooltip
                labelFormatter={(val: unknown) => {
                  if (typeof val !== 'string') return String(val ?? '');
                  const d = new Date(val);
                  return d.toLocaleDateString('es-AR', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  });
                }}
                formatter={(value: unknown) => [Number(value), 'Acciones']}
              />
              <Bar
                dataKey="total"
                fill="#3b82f6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default AccionesPorDiaChart;
