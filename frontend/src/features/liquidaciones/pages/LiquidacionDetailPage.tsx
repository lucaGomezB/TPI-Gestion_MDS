import { useState } from 'react';
import { useParams } from 'react-router-dom';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import CerrarLiquidacionModal from '../components/CerrarLiquidacionModal';
import { useLiquidacionDetail } from '../hooks/useLiquidaciones';

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount);
}

function LiquidacionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [showCerrarModal, setShowCerrarModal] = useState(false);

  const { data, isLoading, isError, refetch } = useLiquidacionDetail(id ?? '');

  if (isLoading) return <Loading skeleton />;
  if (isError) return <ErrorDisplay message="Error al cargar detalle" onRetry={() => void refetch()} />;
  if (!data) return <ErrorDisplay message="Liquidacion no encontrada" />;

  const isClosed = data.estado === 'cerrada';

  return (
    <div>
      <PageHeader
        title={`Liquidacion - ${data.periodo}`}
        breadcrumbs={[
          { label: 'Liquidaciones', href: '/liquidaciones' },
          { label: data.periodo },
        ]}
        actions={
          !isClosed
            ? [{ label: 'Cerrar liquidacion', onClick: () => setShowCerrarModal(true) }]
            : undefined
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Info card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Informacion general</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Periodo:</span>
              <p className="font-medium">{data.periodo}</p>
            </div>
            <div>
              <span className="text-gray-500">Rol:</span>
              <p className="font-medium">{data.rol}</p>
            </div>
            <div>
              <span className="text-gray-500">Cohorte:</span>
              <p className="font-medium">{data.cohorte_id}</p>
            </div>
            <div>
              <span className="text-gray-500">Estado:</span>
              <span className={`inline-flex ml-1 px-2 py-1 text-xs font-medium rounded-full ${
                isClosed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {data.estado}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Cerrada el:</span>
              <p className="font-medium">{data.cerrada_at || '-'}</p>
            </div>
            <div>
              <span className="text-gray-500">Es NEXO:</span>
              <p className="font-medium">{data.es_nexo ? 'Si' : 'No'}</p>
            </div>
          </div>
        </div>

        {/* Amounts card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Montos</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Salario base:</span>
              <span className="font-medium">{formatCurrency(data.monto_base)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Plus aplicados:</span>
              <span className="font-medium">{formatCurrency(data.monto_plus)}</span>
            </div>
            <hr className="border-gray-200" />
            <div className="flex justify-between text-base font-semibold">
              <span>Total:</span>
              <span>{formatCurrency(data.total)}</span>
            </div>
          </div>

          {data.comisiones.length > 0 && (
            <div>
              <span className="text-sm text-gray-500">Comisiones a cargo:</span>
              <p className="text-sm font-medium">{data.comisiones.join(', ')}</p>
            </div>
          )}
        </div>
      </div>

      {/* Desglose Base */}
      {data.desglose_base && Object.keys(data.desglose_base).length > 0 && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Desglose - Salario base</h3>
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(data.desglose_base, null, 2)}
          </pre>
        </div>
      )}

      {/* Desglose Plus */}
      {data.desglose_plus && data.desglose_plus.length > 0 && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Desglose - Plus aplicados</h3>
          <div className="space-y-2">
            {data.desglose_plus.map((plus, idx) => (
              <pre key={idx} className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md whitespace-pre-wrap">
                {JSON.stringify(plus, null, 2)}
              </pre>
            ))}
          </div>
        </div>
      )}

      {showCerrarModal && (
        <CerrarLiquidacionModal
          liquidacionId={data.id}
          isOpen={showCerrarModal}
          onClose={() => setShowCerrarModal(false)}
          onSuccess={() => void refetch()}
        />
      )}
    </div>
  );
}

export default LiquidacionDetailPage;
