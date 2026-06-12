import type { LiquidacionKPI as LiquidacionKPIType } from '../types';

interface LiquidacionKPIProps {
  kpis: LiquidacionKPIType;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount);
}

function LiquidacionKPI({ kpis }: LiquidacionKPIProps) {
  const cards = [
    { label: 'Total sin factura', value: kpis.total_sin_factura, color: 'bg-blue-50 text-blue-800 border-blue-200' },
    { label: 'Total con factura', value: kpis.total_con_factura, color: 'bg-amber-50 text-amber-800 border-amber-200' },
    { label: 'Total general', value: kpis.total_general, color: 'bg-green-50 text-green-800 border-green-200' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      {cards.map((card) => (
        <div key={card.label} className={`rounded-lg border p-4 ${card.color}`}>
          <p className="text-sm font-medium opacity-75">{card.label}</p>
          <p className="text-2xl font-bold mt-1">{formatCurrency(card.value)}</p>
        </div>
      ))}
    </div>
  );
}

export default LiquidacionKPI;
