import { useState } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import AbonarFacturaModal from '../components/AbonarFacturaModal';
import { useFacturasAdmin } from '../hooks/useFacturas';
import { getDescargarFacturaUrl } from '../services/facturaService';

function FacturasAdminPage() {
  const [estado, setEstado] = useState('');
  const [periodo, setPeriodo] = useState('');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [abonarModal, setAbonarModal] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useFacturasAdmin({
    estado: estado || undefined,
    periodo: periodo || undefined,
    q: q || undefined,
    page,
    page_size: 50,
  });

  return (
    <div>
      <PageHeader
        title="Facturas"
        breadcrumbs={[
          { label: 'Administracion', href: '/' },
          { label: 'Facturas' },
        ]}
      />

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div>
            <label htmlFor="filtro-estado" className="block text-xs font-medium text-gray-500 mb-1">
              Estado
            </label>
            <select
              id="filtro-estado"
              value={estado}
              onChange={(e) => { setEstado(e.target.value); setPage(1); }}
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="Pendiente">Pendiente</option>
              <option value="Abonada">Abonada</option>
            </select>
          </div>

          <div>
            <label htmlFor="filtro-periodo" className="block text-xs font-medium text-gray-500 mb-1">
              Periodo
            </label>
            <input
              id="filtro-periodo"
              type="month"
              value={periodo}
              onChange={(e) => { setPeriodo(e.target.value); setPage(1); }}
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="sm:col-span-2">
            <label htmlFor="filtro-q" className="block text-xs font-medium text-gray-500 mb-1">
              Buscar en detalle
            </label>
            <input
              id="filtro-q"
              type="text"
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }}
              placeholder="Buscar..."
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {isLoading && <Loading skeleton />}
      {isError && <ErrorDisplay message="Error al cargar facturas" onRetry={() => void refetch()} />}

      {data && data.items.length === 0 && (
        <EmptyState title="Sin facturas" description="No se encontraron facturas con los filtros actuales." />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periodo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Docente</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detalle</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Tamaño</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.items.map((factura) => (
                  <tr key={factura.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{factura.periodo}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{factura.usuario_id}</td>
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
                    <td className="px-4 py-3 text-right space-x-2">
                      <a
                        href={getDescargarFacturaUrl(factura.id)}
                        className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Descargar
                      </a>
                      {factura.estado === 'Pendiente' && (
                        <button
                          onClick={() => setAbonarModal(factura.id)}
                          className="text-sm text-green-600 hover:text-green-800 transition-colors"
                        >
                          Abonar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.total > data.page_size && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                Mostrando {(data.page - 1) * data.page_size + 1} - {Math.min(data.page * data.page_size, data.total)} de {data.total}
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 hover:bg-gray-50 transition-colors"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * 50 >= data.total}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 hover:bg-gray-50 transition-colors"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {abonarModal && (
        <AbonarFacturaModal
          facturaId={abonarModal}
          isOpen={!!abonarModal}
          onClose={() => setAbonarModal(null)}
          onSuccess={() => void refetch()}
        />
      )}
    </div>
  );
}

export default FacturasAdminPage;
