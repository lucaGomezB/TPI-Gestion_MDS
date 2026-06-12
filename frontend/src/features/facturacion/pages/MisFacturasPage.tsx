import { useState } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import SubirFacturaModal from '../components/SubirFacturaModal';
import { useMisFacturas } from '../hooks/useFacturas';
import { getDescargarFacturaUrl } from '../services/facturaService';

function MisFacturasPage() {
  const [periodo, setPeriodo] = useState('');
  const [page, setPage] = useState(1);
  const [showSubirModal, setShowSubirModal] = useState(false);

  const { data, isLoading, isError, refetch } = useMisFacturas({
    periodo: periodo || undefined,
    page,
    page_size: 50,
  });

  return (
    <div>
      <PageHeader
        title="Mis Facturas"
        actions={[{ label: 'Subir factura', onClick: () => setShowSubirModal(true) }]}
      />

      <div className="mb-6 flex items-center space-x-2">
        <label htmlFor="mis-facturas-periodo" className="text-sm font-medium text-gray-700">
          Filtrar por periodo:
        </label>
        <input
          id="mis-facturas-periodo"
          type="month"
          value={periodo}
          onChange={(e) => { setPeriodo(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {periodo && (
          <button
            onClick={() => { setPeriodo(''); setPage(1); }}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Limpiar
          </button>
        )}
      </div>

      {isLoading && <Loading skeleton />}
      {isError && <ErrorDisplay message="Error al cargar facturas" onRetry={() => void refetch()} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title="Sin facturas"
          description="No has subido facturas aun."
          actionLabel="Subir factura"
          onAction={() => setShowSubirModal(true)}
        />
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periodo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalle</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Tamaño</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subida</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Accion</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.items.map((factura) => (
                <tr key={factura.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">{factura.periodo}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">{factura.detalle}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 text-right">{factura.tamano_kb.toFixed(0)} KB</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      factura.estado === 'Abonada'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {factura.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{factura.cargada_at}</td>
                  <td className="px-4 py-3 text-right">
                    <a
                      href={getDescargarFacturaUrl(factura.id)}
                      className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Descargar
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showSubirModal && (
        <SubirFacturaModal
          isOpen={showSubirModal}
          onClose={() => setShowSubirModal(false)}
        />
      )}
    </div>
  );
}

export default MisFacturasPage;
