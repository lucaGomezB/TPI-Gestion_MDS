import { useState } from 'react';
import PageHeader from '@/shared/components/PageHeader';
import Loading from '@/shared/components/Loading';
import ErrorDisplay from '@/shared/components/ErrorDisplay';
import EmptyState from '@/shared/components/EmptyState';
import { Link } from 'react-router-dom';
import { useHistorial } from '../hooks/useLiquidaciones';

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
    minimumFractionDigits: 2,
  }).format(amount);
}

function HistorialPage() {
  const [periodo, setPeriodo] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useHistorial({
    periodo: periodo || undefined,
    page,
    page_size: 50,
  });

  return (
    <div>
      <PageHeader
        title="Historial de liquidaciones"
        breadcrumbs={[
          { label: 'Liquidaciones', href: '/liquidaciones' },
          { label: 'Historial' },
        ]}
      />

      <div className="mb-6 flex items-center space-x-2">
        <label htmlFor="historial-periodo" className="text-sm font-medium text-gray-700">
          Filtrar por periodo:
        </label>
        <input
          id="historial-periodo"
          type="month"
          value={periodo}
          onChange={(e) => {
            setPeriodo(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {periodo && (
          <button
            onClick={() => {
              setPeriodo('');
              setPage(1);
            }}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Limpiar
          </button>
        )}
      </div>

      {isLoading && <Loading skeleton />}
      {isError && <ErrorDisplay message="Error al cargar historial" onRetry={() => void refetch()} />}

      {data && data.items.length === 0 && (
        <EmptyState title="Sin historial" description="No hay liquidaciones cerradas en este periodo." />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periodo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Docente</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rol</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cerrada</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Accion</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{item.periodo}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.usuario_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.rol}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">
                      {formatCurrency(item.total)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.cerrada_at || '-'}</td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        to={`/liquidaciones/${item.id}`}
                        className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        Ver
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
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
                  disabled={data.page * data.page_size >= data.total}
                  className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 hover:bg-gray-50 transition-colors"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default HistorialPage;
