import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
}

function MetricCard({ label, value, trend, trendLabel }: MetricCardProps): ReactNode {
  const trendColors: Record<string, string> = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-sm font-medium text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {trend && (
        <p className={`text-xs mt-1 ${trendColors[trend]}`}>
          {trend === 'up' && '\u2191 '}
          {trend === 'down' && '\u2193 '}
          {trendLabel || ''}
        </p>
      )}
    </div>
  );
}

export default MetricCard;
