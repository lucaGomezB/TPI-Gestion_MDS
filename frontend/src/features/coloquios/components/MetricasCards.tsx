import { type ReactNode } from 'react';
import type { MetricasColoquio } from '../types/coloquioTypes';

interface MetricasCardsProps {
  metricas: MetricasColoquio;
}

interface KpiCardProps {
  label: string;
  value: number;
}

function KpiCard({ label, value }: KpiCardProps): ReactNode {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

function MetricasCards({ metricas }: MetricasCardsProps): ReactNode {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard label="Convocatorias activas" value={metricas.total_convocatorias_activas} />
      <KpiCard label="Alumnos importados" value={metricas.total_alumnos_importados} />
      <KpiCard label="Reservas activas" value={metricas.total_reservas_activas} />
      <KpiCard label="Resultados registrados" value={metricas.total_resultados_registrados} />
    </div>
  );
}

export default MetricasCards;
