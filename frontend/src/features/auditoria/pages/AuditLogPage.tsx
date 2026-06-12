import { type ReactNode } from 'react';
import { useAuditLog } from '../hooks/useAuditLog';
import AuditFilters from '../components/AuditFilters';
import AuditLogTable from '../components/AuditLogTable';
import AuditPagination from '../components/AuditPagination';
import AuditExportButton from '../components/AuditExportButton';
import PageHeader from '../../../shared/components/PageHeader';
import Loading from '../../../shared/components/Loading';
import ErrorDisplay from '../../../shared/components/ErrorDisplay';
import EmptyState from '../../../shared/components/EmptyState';

function AuditLogPage(): ReactNode {
  const {
    filters,
    setFilters,
    clearFilters,
    goToPage,
    changePageSize,
    hasActiveFilters,
    data,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,
  } = useAuditLog();

  // Initial state — no search performed yet
  const showInitialEmpty = !isLoading && !isError && !hasActiveFilters;

  // Error state
  if (isError) {
    return (
      <div className="p-6">
        <PageHeader
          title="Log de Auditoría"
          breadcrumbs={[
            { label: 'Administración' },
            { label: 'Auditoría' },
            { label: 'Log de Auditoría' },
          ]}
        />
        <ErrorDisplay
          message={
            error instanceof Error
              ? error.message
              : 'Error al cargar el log de auditoría'
          }
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="p-6">
      <PageHeader
        title="Log de Auditoría"
        breadcrumbs={[
          { label: 'Administración' },
          { label: 'Auditoría' },
          { label: 'Log de Auditoría' },
        ]}
      />

      <AuditFilters
        filters={filters}
        onFilterChange={setFilters}
        onClear={clearFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {/* Initial empty state */}
      {showInitialEmpty && (
        <EmptyState
          title="Realice una búsqueda para ver resultados"
          description="Use el campo de búsqueda o los filtros para consultar el log de auditoría."
        />
      )}

      {/* Loading state (initial load) */}
      {isLoading && <Loading message="Buscando entradas..." />}

      {/* Results */}
      {data && !isLoading && (
        <>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500">
              {data.total} resultado{data.total !== 1 ? 's' : ''}
            </p>
            <AuditExportButton
              filters={filters}
              disabled={data.items.length === 0}
            />
          </div>

          <AuditLogTable
            items={data.items}
            isLoading={isLoading}
            isFetching={isFetching}
          />

          {data.total > 0 && (
            <AuditPagination
              total={data.total}
              offset={filters.offset}
              limit={filters.limit}
              onPageChange={goToPage}
              onPageSizeChange={changePageSize}
            />
          )}
        </>
      )}
    </div>
  );
}

export default AuditLogPage;
