import { useState, useMemo } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import PeriodoFilter from '../components/PeriodoFilter';
import LiquidacionKPI from '../components/LiquidacionKPI';
import LiquidacionTable from '../components/LiquidacionTable';
import { useLiquidacionList } from '../hooks/useLiquidaciones';
import type { Liquidacion } from '../types';

type ViewTab = 'general' | 'nexo' | 'facturadores';

function getCurrentPeriodo(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function LiquidacionesPage() {
  const [periodo, setPeriodo] = useState(getCurrentPeriodo);
  const [viewTab, setViewTab] = useState<ViewTab>('general');

  const { data, isLoading, isError, refetch } = useLiquidacionList({ periodo, page_size: 200 });

  const { generalItems, nexoItems, facturadoresItems } = useMemo(() => {
    if (!data?.items) return { generalItems: [], nexoItems: [], facturadoresItems: [] };

    const general: Liquidacion[] = [];
    const nexo: Liquidacion[] = [];
    const facturadores: Liquidacion[] = [];

    for (const item of data.items) {
      if (item.es_nexo) {
        nexo.push(item);
      } else if (item.excluido_por_factura) {
        facturadores.push(item);
      } else {
        general.push(item);
      }
    }

    return { generalItems: general, nexoItems: nexo, facturadoresItems: facturadores };
  }, [data]);

  const currentItems = viewTab === 'general' ? generalItems : viewTab === 'nexo' ? nexoItems : facturadoresItems;

  const tabs: { key: ViewTab; label: string; count: number }[] = [
    { key: 'general', label: 'General', count: generalItems.length },
    { key: 'nexo', label: 'NEXO', count: nexoItems.length },
    { key: 'facturadores', label: 'Facturadores', count: facturadoresItems.length },
  ];

  return (
    <div>
      <PageHeader
        title="Liquidaciones"
        breadcrumbs={[{ label: 'Liquidaciones' }]}
      />

      <div className="flex items-center justify-between mb-6">
        <PeriodoFilter value={periodo} onChange={setPeriodo} />
      </div>

      {isLoading && <Loading skeleton />}
      {isError && <ErrorDisplay message="Error al cargar liquidaciones" onRetry={() => void refetch()} />}

      {data && (
        <>
          <LiquidacionKPI kpis={data.kpis} />

          {/* F10.6: NEXO + Facturadores tabbed view */}
          <div className="border-b border-gray-200 mb-4">
            <nav className="flex space-x-6" aria-label="Vista">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setViewTab(tab.key)}
                  className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                    viewTab === tab.key
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </nav>
          </div>

          <LiquidacionTable items={currentItems} />
        </>
      )}
    </div>
  );
}

export default LiquidacionesPage;
